import asyncio
import json
import os
import shutil
from tempfile import mkdtemp
from typing import AsyncGenerator, Iterator

import aiohttp
from loguru import logger

CHUNK_SIZE = 256 * 1024  # 256 KB


class Downloader:
    def __init__(
        self,
        url: str,
        filename: str,
        part_size: int = 10 * 1024 * 1024,
        max_connections: int = 5,
    ):
        self.url = url
        self.filename = filename
        self.part_size = part_size
        self.max_connections = max_connections

        self.temp_dir = f"{filename}.parts"
        self.meta_file = f"{filename}.meta"

        self.file_size: int | None = None
        self.parts: list[dict] = []

    # -------------------------
    # Public API
    # -------------------------
    async def download(self) -> AsyncGenerator[float, None]:
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=60)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            if not await self._check_range_support(session):
                logger.warning("Range not supported → single download")
                async for p in self._download_single(session):
                    yield p
                return

            self._prepare_parts()

            try:
                async for p in self._download_multipart(session):
                    yield p
            except Exception as e:
                logger.error(f"Multipart failed: {e}")
                logger.warning("Fallback to single download")
                async for p in self._download_single(session):
                    yield p

    # -------------------------
    # Range check + size
    # -------------------------
    async def _check_range_support(self, session) -> bool:
        try:
            async with session.get(self.url, headers={"Range": "bytes=0-0"}) as resp:
                if resp.status != 206:
                    return False
                self.file_size = int(resp.headers["Content-Range"].split("/")[-1])
                return True
        except Exception:
            return False

    # -------------------------
    # Resume state
    # -------------------------
    def _prepare_parts(self):
        os.makedirs(self.temp_dir, exist_ok=True)

        if os.path.exists(self.meta_file):
            self._load_state()
            logger.info("Resume detected")
            return

        parts = (self.file_size // self.part_size) + 1
        self.parts = []

        for i in range(parts):
            start = i * self.part_size
            end = min(start + self.part_size - 1, self.file_size - 1)
            self.parts.append(
                {
                    "id": i,
                    "start": start,
                    "end": end,
                    "done": False,
                }
            )

        self._save_state()

    def _save_state(self):
        with open(self.meta_file, "w") as f:
            json.dump(
                {
                    "file_size": self.file_size,
                    "parts": self.parts,
                },
                f,
            )

    def _load_state(self):
        with open(self.meta_file) as f:
            data = json.load(f)
        self.file_size = data["file_size"]
        self.parts = data["parts"]

        for part in self.parts:
            part_file = self._part_path(part["id"])
            if os.path.exists(part_file):
                part["done"] = True

    # -------------------------
    # Multipart download
    # -------------------------
    async def _download_multipart(self, session) -> AsyncGenerator[float, None]:
        semaphore = asyncio.Semaphore(self.max_connections)

        total_downloaded = sum(
            os.path.getsize(self._part_path(p["id"])) for p in self.parts if p["done"]
        )

        async def runner(part):
            async with semaphore:
                if part["done"]:
                    return 0
                return await self._fetch_part(session, part)

        tasks = [runner(p) for p in self.parts]

        for coro in asyncio.as_completed(tasks):
            downloaded = await coro
            total_downloaded += downloaded
            yield total_downloaded / self.file_size * 100

        self._join_parts()
        self.cleanup()
        yield 100.0

    async def _fetch_part(self, session, part) -> int:
        headers = {"Range": f"bytes={part['start']}-{part['end']}"}
        part_file = self._part_path(part["id"])

        async with session.get(self.url, headers=headers) as resp:
            if resp.status != 206:
                raise RuntimeError("Range lost")

            downloaded = 0
            with open(part_file, "wb") as f:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)

        part["done"] = True
        self._save_state()
        return downloaded

    # -------------------------
    # Single download
    # -------------------------
    async def _download_single(self, session) -> AsyncGenerator[float, None]:
        async with session.get(self.url) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0

            with open(self.filename, "wb") as f:
                async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        yield downloaded / total * 100

        yield 100.0

    # -------------------------
    # Join + cleanup
    # -------------------------
    def _join_parts(self):
        with open(self.filename, "wb") as out:
            for part in self.parts:
                with open(self._part_path(part["id"]), "rb") as pf:
                    shutil.copyfileobj(pf, out)

    def cleanup(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        if os.path.exists(self.meta_file):
            os.remove(self.meta_file)

    def _part_path(self, part_id: int) -> str:
        return os.path.join(self.temp_dir, f"part{part_id}")


# -------------------------
# Sync wrapper
# -------------------------
def download(url: str, filename: str) -> Iterator[float]:
    async def run():
        d = Downloader(url, filename)
        async for p in d.download():
            yield p

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agen = run()

    try:
        while True:
            yield loop.run_until_complete(agen.__anext__())
    except StopAsyncIteration:
        pass
    finally:
        loop.close()

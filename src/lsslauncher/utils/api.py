import gzip
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple

import httpx
from loguru import logger
from utils.download import download
from utils.helpers import get_folder

APP_DATA_PATH = Path(get_folder()) / "packs"
BASE_URL = "https://lsslauncher.xyz"
TIMEOUT = httpx.Timeout(10.0)


class API:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.client = httpx.Client(
            base_url=BASE_URL,
            timeout=TIMEOUT,
            verify=True,  # enforce HTTPS TLS verification
        )
        logger.info("API instance created")

    # --------------------
    # Internal helpers
    # --------------------

    def _auth_headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        headers = {"accept": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        if extra:
            headers.update(extra)
        return headers

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Tuple[int, dict]:
        try:
            response = self.client.request(
                method,
                endpoint,
                headers=headers,
                **kwargs,
            )
            logger.info(f"{method.upper()} {endpoint} -> {response.status_code}")
            try:
                return response.status_code, response.json()
            except ValueError:
                logger.error("Invalid JSON response")
                return response.status_code, {}
        except httpx.HTTPError as exc:
            logger.error(f"HTTP error: {exc}")
            return 0, {}

    # --------------------
    # Auth
    # --------------------

    def get_token(self, login: str, password: str, hwid: str) -> int:
        logger.info(f"Requesting token for user='{login}' hwid='{hwid}'")

        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "username": login,
            "password": password,
            "hwid": hwid,
        }

        status, payload = self._request(
            "POST",
            "/auth/token",
            headers=headers,
            data=data,
        )

        if status == 200:
            self.token = (
                f"{payload['token_type'].capitalize()} {payload['access_token']}"
            )
            logger.success("Token successfully obtained")
            return 200

        detail = payload.get("detail")
        if detail == "Incorrect username or password":
            return 401
        if detail == "Invalid HWID":
            return 409

        return status

    def get_me(self, hwid: str) -> Tuple[int, dict]:
        headers = self._auth_headers({"x-hwid": hwid})
        return self._request("GET", "/users/me", headers=headers)

    # --------------------
    # Files
    # --------------------

    def get_files(self, skip: int, limit: int) -> Tuple[int, dict]:
        headers = self._auth_headers()
        return self._request(
            "GET",
            "/files/",
            headers=headers,
            params={"skip": skip, "limit": limit},
        )

    def get_file(self, file_id: int) -> Tuple[int, dict]:
        headers = self._auth_headers()
        return self._request("GET", f"/files/{file_id}", headers=headers)

    # --------------------
    # Download
    # --------------------

    def download_file(
        self,
        url: str,
        name: str,
        expected_md5: Optional[str],
    ) -> Iterator[float]:
        APP_DATA_PATH.mkdir(parents=True, exist_ok=True)

        local_path = APP_DATA_PATH / name
        gz_path = local_path.with_suffix(local_path.suffix + ".gz")

        if local_path.exists():
            if expected_md5 and self._check_md5(local_path, expected_md5):
                logger.info("File already exists and hash matches")
                return
            elif not expected_md5:
                logger.info("File already exists")
                return

        for progress in download(url, str(gz_path)):
            yield progress

        with gzip.open(gz_path, "rb") as src, open(local_path, "wb") as dst:
            shutil.copyfileobj(src, dst)

        gz_path.unlink(missing_ok=True)
        logger.success(f"Downloaded and extracted '{name}'")

    @staticmethod
    def _check_md5(path: Path, expected: str) -> bool:
        md5 = hashlib.md5()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5.update(chunk)
        return md5.hexdigest() == expected

    # --------------------
    # Tasks
    # --------------------

    def merge_pack(self, s3_key_main: str, s3_key_second: str) -> Tuple[int, str]:
        headers = self._auth_headers()
        status, payload = self._request(
            "POST",
            "/files/merge",
            headers=headers,
            json={
                "first_key": s3_key_main,
                "second_key": s3_key_second,
            },
        )
        return status, payload.get("id", "")

    def get_task_status(self, task_id: str) -> Tuple[int, dict]:
        headers = self._auth_headers()
        return self._request("GET", f"/task/{task_id}", headers=headers)

    # --------------------
    # Cleanup
    # --------------------

    def close(self):
        self.client.close()

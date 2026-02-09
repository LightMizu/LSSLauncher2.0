import threading
import time
import webbrowser
from typing import Any, Dict, List

import webview
from webview.window import Window


class PyWebAPI:
    def __init__(self):
        self.logged_in = False
        self.favorites = set()
        self.installed_packs = set()

    # =====================
    # GENERAL
    # =====================

    def get_about_data(self):
        return {
            "appName": "LSS Launcher",
            "logoLetter": "L",
            "team": [
                {
                    "name": "Alex",
                    "role": "Developer",
                    "color": "bg-purple-500",
                },
                {
                    "name": "Kate",
                    "role": "Designer",
                },
            ],
            "changelog": [
                {
                    "version": "1.2.0",
                    "date": "2026-02-01",
                    "changes": [
                        "Added pack mixing",
                        "Improved launcher performance",
                        "UI polish",
                    ],
                },
                {
                    "version": "1.1.0",
                    "date": "2026-01-15",
                    "changes": [
                        "Favorites support",
                        "Telegram integration",
                    ],
                },
            ],
            "socials": [
                {
                    "id": "github",
                    "title": "GitHub",
                    "icon": "github",
                },
                {
                    "id": "telegram",
                    "title": "Telegram",
                    "icon": "telegram",
                },
                {
                    "id": "website",
                    "title": "Website",
                    "icon": "website",
                },
            ],
        }

    def open_telegram(self):
        webbrowser.open("https://t.me/your_channel")

    def action(self, name: str, payload=None):
        print(f"ACTION: {name}", payload)
        return {"ok": True}

    # =====================
    # SHOP
    # =====================

    def get_shop_items(self):
        return [
            {
                "id": "visual_pack_1",
                "name": "Ultra Visuals",
                "size": "250 MB",
                "category": "visual",
                "isFavorite": False,
            },
            {
                "id": "audio_pack_1",
                "name": "Immersive Sounds",
                "size": "120 MB",
                "category": "audio",
                "isFavorite": True,
            },
        ]

    def get_installed_packs(self) -> List[str]:
        return list(self.installed_packs)

    def get_favorites(self) -> List[str]:
        return list(self.favorites)

    # =====================
    # LOGIN MENU
    # =====================

    def is_login(self) -> bool:
        return True

    def log(*args):
        print(*args)

    def login(self, username: str, password: str, remember: bool) -> int:
        if username == "admin" and password == "admin":
            self.logged_in = True
            return 200  # success
        return 0  # error

    def create_account(self):
        print("Create account clicked")

    # =====================
    # MIX MENU
    # =====================

    def start_mix(self, mainId: str, subId: str):
        def worker():
            time.sleep(3)
            webview.active_window().evaluate_js(
                f'window.__lsslauncher_on_mix_ready?.("merge")'
            )

        threading.Thread(target=worker, daemon=True).start()

    def dowload_mix(self):
        def worker():
            for i in range(0, 101, 10):
                time.sleep(0.3)
                webview.active_window().evaluate_js(
                    f"window.__lsslauncher_on_mix_progress?.({i})"
                )

            webview.active_window().evaluate_js("window.__lsslauncher_on_mix_done?.()")

        threading.Thread(target=worker, daemon=True).start()

    def cancel_mix(self):
        print("Mix canceled")

    # =====================
    # HOME MENU
    # =====================
    def close(self):
        webview.active_window().destroy()

    def minimize(self):
        webview.active_window().minimize()

    def launch_game(self):
        print("Launching game")

    def install_game(self):
        print("Installing game")

    def update_fix(self):
        print("Updating fix")

    def uninstall_game(self):
        print("Uninstalling game")

    def download_pack(self, id: str):
        def worker():
            for p in range(0, 101, 20):
                time.sleep(0.2)
                webview.active_window().evaluate_js(
                    f"window.__lsslauncher_on_download_progress?.('{id}', {p})"
                )

            webview.active_window().evaluate_js(
                f"window.__lsslauncher_on_download_done?.('{id}')"
            )

        threading.Thread(target=worker, daemon=True).start()

    def install_pack(self, id: str):
        self.installed_packs.add(id)

    def toggle_favorite(self, id: str, isFavorite: bool):
        if isFavorite:
            self.favorites.add(id)
        else:
            self.favorites.discard(id)

    def open_pack_screenshots(self, id: str):
        print(f"Open screenshots for {id}")

    def add_custom_pack(self):
        print("Add custom pack")


js_api = PyWebAPI()

window = webview.create_window(
    "LSS Launcher",
    "C:\\Users\\InfSec-10\\Documents\\Project\\LSSLauncherFront\\dist\\index.html",
    js_api=js_api,  # временно
    frameless=True,
    easy_drag=False,
    min_size=(1000, 700),
)
assert window
webview.start(http_server=True)

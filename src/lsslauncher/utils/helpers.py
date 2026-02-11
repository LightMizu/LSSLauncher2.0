import uuid
import subprocess
import platform
import sys
import os
from loguru import logger

def find_by_key(items, key, value) -> dict[str, str]|None:
    return next((item for item in items if item.get(key) == value), None) 

def get_uuid_file(id) -> str:
    namespace = uuid.NAMESPACE_DNS
    uuids = str(uuid.uuid5(namespace, str(id)))
    logger.debug(f"Getting uuid 4 {id} => {uuids}")
    return uuids

def human_readable_size(num_bytes: int, decimal_places: int = 2) -> str:
    """
    Преобразует число байтов в удобный для чтения формат.
    
    :param num_bytes: количество байтов
    :param decimal_places: количество знаков после запятой
    :return: строка вида '10.23 MB'
    """
    calc_bytes = num_bytes
    if calc_bytes < 0:
        raise ValueError("Размер не может быть отрицательным")
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
        if calc_bytes < 1000:
            return f"{calc_bytes:.{decimal_places}f} {unit}"
        calc_bytes /= 1000
    return f"{calc_bytes:.{decimal_places}f} PB"


def open_folder(path):
    
    if platform.system() == "Windows":
        subprocess.Popen(["explorer", path])
    elif platform.system() == "Darwin":  # macOS
        subprocess.Popen(["open", path])
    else:  # Linux
        subprocess.Popen(["xdg-open", path])

def get_folder():
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        bundle_dir = os.path.dirname(sys.executable)
    else:
        # we are running in a normal Python environment
        bundle_dir = os.path.abspath(".")
    logger.info(f"Bundel folder: {bundle_dir}")
    return bundle_dir

import os
import platform
from functools import lru_cache

import pandas as pd
import psutil

GIB = 1024 ** 3
LOW_PERCENT = 15


def capacity(remaining, total):
    if pd.isna(remaining) or pd.isna(total) or total <= 0:
        return "Unavailable", "Reading unavailable"
    percent = 100 * remaining / total
    status = "Low" if percent < LOW_PERCENT else "OK"
    detail = f"{remaining:.1f} of {total:.1f} GiB ({percent:.1f}%)"
    return status, detail


@lru_cache(maxsize=1)
def computer_details():
    cpu_name = platform.processor() or "Unavailable"
    if platform.system() == "Windows":
        import winreg

        key_path = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            cpu_name = name.strip() or cpu_name
        except OSError:
            pass  # The processor identifier above is still usable.

    return {
        "CPU": cpu_name,
        "Logical processors": psutil.cpu_count(logical=True) or "Unavailable",
        "Operating system and build": f"{platform.system()} {platform.version()}",
    }


def read_live():
    cpu = psutil.cpu_percent(interval=0.2)
    ram = psutil.virtual_memory()
    try:
        drive = psutil.disk_usage(os.environ["SystemRoot"])
    except (KeyError, OSError):
        drive = None

    return {
        "cpu_pct": cpu,
        "ram_available_gib": ram.available / GIB,
        "ram_total_gib": ram.total / GIB,
        "disk_free_gib": drive.free / GIB if drive else None,
        "disk_total_gib": drive.total / GIB if drive else None,
    }


if __name__ == "__main__":
    from pprint import pprint

    pprint(computer_details())
    reading = read_live()
    pprint(reading)
    status, detail = capacity(reading["disk_free_gib"], reading["disk_total_gib"])
    print(f"Windows drive — {status} · {detail}")
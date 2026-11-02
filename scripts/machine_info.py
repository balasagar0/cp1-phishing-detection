"""This machine's CPU, RAM and OS, for run records (workbook, benchmark, preflight).  python scripts/machine_info.py"""
import os, platform, sys, json


def cpu_name():
    if sys.platform == "win32":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0") as k:
                return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except OSError: pass
    try:
        for line in open("/proc/cpuinfo"):
            if line.lower().startswith("model name"): return line.split(":", 1)[1].strip()
    except OSError: pass
    return platform.processor() or platform.machine()


def ram_gb():
    if sys.platform == "win32":
        import ctypes
        class MS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong), ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong), ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong), ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
        m = MS(); m.dwLength = ctypes.sizeof(MS)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m)): return round(m.ullTotalPhys / 2 ** 30, 1)
    try:
        for line in open("/proc/meminfo"):
            if line.startswith("MemTotal"): return round(int(line.split()[1]) / 2 ** 20, 1)
    except OSError: pass
    return None


def info():
    return {"cpu": cpu_name(), "logical_cpus": os.cpu_count(), "ram_gb": ram_gb(), "os": platform.platform(), "python": platform.python_version(), "machine": platform.node()}


def one_line(i=None):
    i = i or info()
    return f"{i['cpu']} ({i['logical_cpus']} logical CPUs), {i['ram_gb']} GB RAM, {i['os']}, Python {i['python']}"


if __name__ == "__main__":
    print(json.dumps(info(), indent=1)); print(one_line())

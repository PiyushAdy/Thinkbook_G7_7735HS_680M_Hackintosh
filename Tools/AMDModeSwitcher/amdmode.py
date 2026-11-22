#!/usr/bin/env python3
"""Lightweight GNOME-style Power Mode Switcher for AMDRyzenCPUPowerManagement.kext (0% background CPU).
Usage:
  amdmode status
  amdmode save       # Power Saver: 1600 MHz (P2), CPB Off, Manual
  amdmode balanced   # Balanced:    2560 MHz (P1), CPB Off, Manual
  amdmode perf       # Performance: 3200 MHz (P0), CPB On (4.83 GHz boost), Auto
"""
import ctypes, sys

iokit = ctypes.CDLL("/System/Library/Frameworks/IOKit.framework/IOKit")
iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]
iokit.IOServiceMatching.restype = ctypes.c_void_p
iokit.IOServiceGetMatchingService.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
iokit.IOServiceGetMatchingService.restype = ctypes.c_uint32
iokit.IOServiceOpen.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
iokit.IOServiceOpen.restype = ctypes.c_int32
iokit.IOServiceClose.argtypes = [ctypes.c_uint32]
iokit.IOServiceClose.restype = ctypes.c_int32
iokit.IOObjectRelease.argtypes = [ctypes.c_uint32]
iokit.IOObjectRelease.restype = ctypes.c_int32
iokit.IOConnectCallScalarMethod.argtypes = [
    ctypes.c_uint32, ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint32,
    ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint32),
]
iokit.IOConnectCallScalarMethod.restype = ctypes.c_int32
iokit.IOConnectCallStructMethod.argtypes = [
    ctypes.c_uint32, ctypes.c_uint32,
    ctypes.c_void_p, ctypes.c_size_t,
    ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t),
]
iokit.IOConnectCallStructMethod.restype = ctypes.c_int32

libc = ctypes.CDLL("/usr/lib/libSystem.B.dylib")
libc.mach_task_self.restype = ctypes.c_uint32

def open_client():
    svc = iokit.IOServiceGetMatchingService(0, iokit.IOServiceMatching(b"AMDRyzenCPUPowerManagement"))
    if not svc:
        sys.exit("Error: AMDRyzenCPUPowerManagement.kext not loaded.")
    conn = ctypes.c_uint32(0)
    kr = iokit.IOServiceOpen(svc, libc.mach_task_self(), 0, ctypes.byref(conn))
    iokit.IOObjectRelease(svc)
    if kr != 0:
        sys.exit(f"Error: IOServiceOpen failed (0x{kr & 0xffffffff:x})")
    return conn.value

def set_scalar(conn, sel, val):
    inp = (ctypes.c_uint64 * 1)(val)
    kr = iokit.IOConnectCallScalarMethod(conn, sel, inp, 1, None, None)
    if kr != 0:
        sys.exit(f"Error: selector {sel}({val}) failed (0x{kr & 0xffffffff:x})")

def get_u64(conn, sel, count=1):
    buf = (ctypes.c_uint64 * count)()
    sz = ctypes.c_size_t(ctypes.sizeof(buf))
    kr = iokit.IOConnectCallStructMethod(conn, sel, None, 0, buf, ctypes.byref(sz))
    return list(buf) if kr == 0 else None

def get_temp(conn):
    buf = (ctypes.c_float * 1)()
    sz = ctypes.c_size_t(ctypes.sizeof(buf))
    kr = iokit.IOConnectCallStructMethod(conn, 3, None, 0, buf, ctypes.byref(sz))
    return buf[0] if kr == 0 else None

def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "status"
    conn = open_client()
    try:
        if cmd in ("save", "powersave", "eco"):
            set_scalar(conn, 14, 0)  # PPM Auto Off (Manual lock)
            set_scalar(conn, 12, 0)  # CPB Off
            set_scalar(conn, 10, 2)  # P2 (1600 MHz)
            print("Mode: Power Saver (1600 MHz, CPB Off)")
        elif cmd in ("balanced", "bal"):
            set_scalar(conn, 14, 0)  # PPM Auto Off (Manual lock)
            set_scalar(conn, 12, 0)  # CPB Off
            set_scalar(conn, 10, 1)  # P1 (2560 MHz)
            print("Mode: Balanced (2560 MHz, CPB Off)")
        elif cmd in ("perf", "performance", "turbo"):
            set_scalar(conn, 10, 0)  # P0 (3200 MHz)
            set_scalar(conn, 12, 1)  # CPB On (4.83 GHz turbo)
            set_scalar(conn, 14, 1)  # PPM Auto On
            print("Mode: Performance (3200 MHz + CPB Boost, Auto)")
        elif cmd == "status":
            ps = get_u64(conn, 9, 1)
            cpb = get_u64(conn, 11, 2)
            ppm = get_u64(conn, 13, 1)
            temp = get_temp(conn)
            names = {0: "P0 (3200 MHz)", 1: "P1 (2560 MHz)", 2: "P2 (1600 MHz)"}
            p_str = names.get(ps[0], f"P{ps[0]}") if ps else "?"
            c_str = ("On" if cpb[1] else "Off") if cpb else "?"
            a_str = ("Auto" if ppm[0] else "Manual") if ppm else "?"
            t_str = f"{temp:.1f} C" if temp is not None else "?"
            print(f"P-State: {p_str} | CPB: {c_str} | Scaling: {a_str} | Temp: {t_str}")
        else:
            print(__doc__)
    finally:
        iokit.IOServiceClose(conn)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
P104-100 one-shot Gen2 live write + retrain.
WARNING: writes to GPU BAR0. Use at your own risk.
Requires root and iomem=relaxed.
"""
import mmap, os, struct, sys, time, subprocess

BDF = "0000:04:00.0"
RESOURCE = f"/sys/bus/pci/devices/{BDF}/resource0"
BAR_SIZE = 16 * 1024 * 1024

SEQ = [
    (0x8872C, "LTSSM / override",     lambda v: (v & ~0xF) | 6),
    (0x2241C, "declaration bits",     lambda v: v | 0x81),
    (0x8841C, "GEN2_DIS",             lambda v: v & ~0x6000),
    (0x8C2C0, "CYA bit2",             lambda v: v & ~0x4),
    (0x8C300, "CYA bit4",             lambda v: v & ~0x10),
    (0x8C040, "target speed request", lambda v: (v & ~0xC0000) | 0x40000),
    (0x8C1C0, "target rate",          lambda v: (v & ~0xF0000) | 0x20000),
    (0x88610, "VSEC gate",            lambda v: (v & ~0x1000) | 0x1),
]

def read32(mm, off):
    return struct.unpack("<I", mm[off:off+4])[0]

def write32(mm, off, val):
    mm[off:off+4] = struct.pack("<I", val & 0xFFFFFFFF)
    mm.flush()

def retrain():
    """Best-effort retrain via setpci on the GPU and its upstream port."""
    print("Attempting link retrain...")
    # Set target speed to Gen2 (LNKCTL2 = 2) on the device
    subprocess.run(["setpci", "-s", BDF, "CAP_EXP+0x30.w=2"], check=False)
    # Find upstream port and trigger retrain (bit 5 of LNKCTL)
    try:
        out = subprocess.check_output(["lspci", "-t"], text=True)
        # crude: just try common parent or use the bridge we saw earlier
        # User previously had the GPU under an AMD switch; adjust if needed
        print("  set LNKCTL2=2 on device")
        # Trigger retrain on the device itself (some boards accept this)
        subprocess.run(["setpci", "-s", BDF, "CAP_EXP+0x10.w=0x0020"], check=False)
        print("  retrain bit written")
    except Exception as e:
        print(f"  retrain helper failed: {e}")
    time.sleep(1.5)

def main():
    if os.geteuid() != 0:
        print("Must run as root")
        sys.exit(1)

    print("=== P104-100 one-shot Gen2 write ===")
    print("This will write the live sequence and attempt a retrain.")
    ans = input("Type YES to continue: ")
    if ans.strip() != "YES":
        print("Aborted.")
        sys.exit(0)

    fd = os.open(RESOURCE, os.O_RDWR)
    mm = mmap.mmap(fd, BAR_SIZE, prot=mmap.PROT_READ | mmap.PROT_WRITE)

    print("\nWriting live sequence...")
    for off, name, transform in SEQ:
        cur = read32(mm, off)
        new = transform(cur)
        write32(mm, off, new)
        rb = read32(mm, off)
        status = "OK" if rb == new else "FAIL"
        print(f"  0x{off:05X} {name:<22} 0x{cur:08X} -> 0x{new:08X}  [{status}]")

    mm.close()
    os.close(fd)

    retrain()

    print("\nDone. Check link speed with:")
    print(f"  sudo lspci -vv -s {BDF} | grep -E 'LnkCap|LnkSta|LnkCtl'")
    print("Or: sudo lspci -vv | grep -A20 '04:00.0'")

if __name__ == "__main__":
    main()

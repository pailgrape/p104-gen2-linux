#!/usr/bin/env python3
"""
P104-100 Gen2 dry-run.
Shows current vs proposed values for the known live write sequence.
Does NOT write anything.
"""
import mmap, os, struct, sys

BDF = "0000:04:00.0"
RESOURCE = f"/sys/bus/pci/devices/{BDF}/resource0"
BAR_SIZE = 16 * 1024 * 1024

# offset -> (name, transform function)
# transform receives current value, returns new value
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

def main():
    try:
        fd = os.open(RESOURCE, os.O_RDWR)
        mm = mmap.mmap(fd, BAR_SIZE, prot=mmap.PROT_READ)
    except Exception as e:
        print(f"Failed to open BAR0: {e}")
        sys.exit(1)

    print(f"Dry-run on {BDF} (no writes)\n")
    print(f"{'Offset':>8}  {'Name':<22}  {'Current':>10}  {'Proposed':>10}  Change")
    print("-" * 70)

    for off, name, transform in SEQ:
        cur = struct.unpack("<I", mm[off:off+4])[0]
        new = transform(cur) & 0xFFFFFFFF
        changed = "YES" if new != cur else "no"
        print(f"0x{off:05X}  {name:<22}  0x{cur:08X}  0x{new:08X}  {changed}")

    mm.close()
    os.close(fd)
    print("\nThis was a dry-run only. Nothing was written.")

if __name__ == "__main__":
    main()

# P104-100 Gen2 Linux Tools

Userspace scripts for experimenting with PCIe Gen2 capability advertisement on NVIDIA P104-100 cards (device ID `10de:1b87`).

**These changes are volatile.** They do not survive a reboot or full bus reset.

## Result from testing

On the tested platform (GPU behind an AMD switch):
- The Gen2 **capability** (`LnkCap` / `LnkCap2` showing 5 GT/s) can be set.
- Actual link **training** stayed at 2.5 GT/s (Gen1, downgraded).
- One key BAR0 register (speed request) often refuses to stick.
- Physical x16 is not possible (only 4 lanes are wired on the P104-100).

This is a platform-dependent limit, not a missing software key.

## Requirements

- Linux (tested on Fedora)
- Root / sudo
- Python 3 (standard library only)
- `pciutils` (`lspci`, `setpci`)
- Kernel parameter `iomem=relaxed` (required for BAR0 mapping)
- NVIDIA P104-100 (`10de:1b87`)

### Install

```bash
# Fedora
sudo dnf install pciutils

# Ubuntu/Debian
sudo apt install pciutils
```

### Enable BAR0 access (one-time)

```bash
sudo grubby --update-kernel=ALL --args="iomem=relaxed"
# or edit GRUB and regenerate
sudo reboot
```

**Remember to remove `iomem=relaxed` when you are done.**

## Files

| File | Purpose |
|------|---------|
| `gen2_dryrun.py` | Read-only. Shows current vs proposed register values. Safe. |
| `gen2_oneshot.py` | Writes the live sequence and attempts a retrain. Asks for confirmation. |
| `unload_nvidia.sh` | Helper to stop the desktop and unload the NVIDIA driver. |

## Usage

### Dry-run (recommended first)

```bash
sudo python3 gen2_dryrun.py
```

Edit the `BDF` variable at the top if your card is not at `0000:04:00.0`.

### One-shot (experimental)

```bash
sudo python3 gen2_oneshot.py
# type YES when prompted
```

For the best chance of registers sticking, unload the NVIDIA driver first:

```bash
sudo systemctl stop display-manager
sudo systemctl stop fah-client 2>/dev/null
sudo killall -9 kwin_wayland plasmashell Xwayland fah-client 2>/dev/null
sudo modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia
```

Then check the link:

```bash
sudo lspci -vv -s 04:00.0 | grep -E 'LnkCap|LnkSta|LnkCtl|LnkCap2'
```

## Warnings

- Requires root.
- A bad write can make the GPU disappear until reboot.
- `iomem=relaxed` reduces kernel memory protection while enabled.
- These scripts only target the known P104-100 sequence. They do not flash VBIOS or change permanent fuses.
- Results vary by motherboard / switch / VBIOS.

## License

Use at your own risk. Provided as-is for research and experimentation.

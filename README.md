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

## Full procedure (steps)

### 1. Boot to console
```bash
sudo systemctl isolate multi-user.target
```

### 2. Dry-run (safe, no writes)
```bash
cd /path/to/scripts
sudo python3 gen2_dryrun.py
```
Edit the `BDF` variable at the top of the script if your card is not at `0000:04:00.0`.

### 3. Stop background processes holding the GPU
```bash
sudo systemctl stop fah-client
# or
sudo killall -9 fah-client
```
Confirm nothing is left:
```bash
sudo lsof /dev/nvidia* 2>/dev/null
```

### 4. Unload the NVIDIA driver
```bash
sudo modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia
lsmod | grep nvidia   # should show nothing
```
Or use the helper:
```bash
sudo ./unload_nvidia.sh
```

### 5. Run the one-shot
```bash
sudo python3 gen2_oneshot.py
# type YES when prompted
```

### 6. Check the link (and optional retrain)
```bash
sudo lspci -vv -s 04:00.0 | grep -E 'LnkCap|LnkSta|LnkCtl|LnkCap2'
```
If still Gen1, try a manual retrain:
```bash
sudo setpci -s 04:00.0 CAP_EXP+0x30.w=2
sudo setpci -s 03:00.0 CAP_EXP+0x30.w=2
sudo setpci -s 03:00.0 CAP_EXP+0x10.w=0x0020
sleep 2
sudo lspci -vv -s 04:00.0 | grep LnkSta
```
(Replace `03:00.0` with your actual upstream bridge if different.)

### 7. Remove + rescan if still Gen1
```bash
sudo sh -c 'echo 1 > /sys/bus/pci/devices/0000:04:00.0/remove'
sleep 2
sudo sh -c 'echo 1 > /sys/bus/pci/rescan'
sleep 3
sudo lspci -vv -s 04:00.0 | grep -E 'LnkCap|LnkSta'
```

### 8. Repeat if desired
Run the one-shot again, then repeat steps 6 and 7.

### 9. Restore kernel memory protection
```bash
sudo grubby --update-kernel=ALL --remove-args="iomem=relaxed"
```

### 10. Return to normal desktop boot
```bash
sudo systemctl set-default graphical.target
sudo reboot
```
Or for this session only:
```bash
sudo modprobe nvidia
sudo systemctl isolate graphical.target
```

## Files

| File | Purpose |
|------|---------|
| `gen2_dryrun.py` | Read-only. Shows current vs proposed register values. Safe. |
| `gen2_oneshot.py` | Writes the live sequence and attempts a retrain. Asks for confirmation. |
| `unload_nvidia.sh` | Helper to stop the desktop and unload the NVIDIA driver. |

## Warnings

- Requires root.
- A bad write can make the GPU disappear until reboot.
- `iomem=relaxed` reduces kernel memory protection while enabled. Remove it when finished.
- These scripts only target the known P104-100 sequence. They do not flash VBIOS or change permanent fuses.
- Results vary by motherboard / switch / VBIOS.

## License

Use at your own risk. Provided as-is for research and experimentation.

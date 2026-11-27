#!/bin/bash
# Temporary: drop to multi-user and unload NVIDIA driver
# so the GPU BAR is free for raw access testing.
# Re-load later with: sudo modprobe nvidia

set -e

echo "Switching to multi-user target (console)..."
sudo systemctl isolate multi-user.target

echo "Unloading NVIDIA modules..."
sudo modprobe -r nvidia_drm nvidia_modeset nvidia || true

echo "Done. NVIDIA driver is unloaded."
echo "You can now run the probe or other BAR0 tools."
echo ""
echo "To restore the driver later:"
echo "  sudo modprobe nvidia"
echo "  sudo systemctl isolate graphical.target   # or just reboot"

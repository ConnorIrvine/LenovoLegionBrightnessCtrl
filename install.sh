#!/bin/bash
# Installation script for Legion Brightness Control Applet

set -e

echo "=========================================="
echo "Legion Brightness Control - Installer"
echo "=========================================="
echo ""

# Check if brightnessctl is installed
if ! command -v brightnessctl &> /dev/null; then
    echo "ERROR: brightnessctl is not installed!"
    echo ""
    echo "Install it with:"
    echo "  sudo apt install brightnessctl"
    echo ""
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed!"
    exit 1
fi

# Check if GTK3 Python bindings are installed
if ! python3 -c "import gi; gi.require_version('Gtk', '3.0')" 2>/dev/null; then
    echo "ERROR: GTK3 Python bindings not installed!"
    echo ""
    echo "Install them with:"
    echo "  sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0"
    echo ""
    exit 1
fi

echo "✓ All dependencies are installed"
echo ""

# Detect Intel backlight maximum
echo "Detecting Intel backlight maximum value..."
if [ -f "/sys/class/backlight/intel_backlight/max_brightness" ]; then
    INTEL_MAX=$(cat /sys/class/backlight/intel_backlight/max_brightness)
    echo "✓ Detected Intel max brightness: $INTEL_MAX"
    
    # Create config directory and file with detected value
    CONFIG_DIR="$HOME/.config/legion-brightness"
    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_DIR/config.json" <<EOF
{
  "intel_max": $INTEL_MAX,
  "use_pkexec": false,
  "last_brightness": 50
}
EOF
    echo "✓ Configuration file created: $CONFIG_DIR/config.json"
else
    echo "⚠ Could not detect Intel backlight. Using default value of 496."
fi

echo ""

# Make scripts executable
chmod +x brightness_applet.py
chmod +x setup_sudoers.py

# Copy icon to local icons directory
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
cp icon.svg "$ICON_DIR/legion-brightness.svg"
echo "✓ Icon installed at:"
echo "  $ICON_DIR/legion-brightness.svg"
echo ""

# Create desktop entry
DESKTOP_FILE="$HOME/.local/share/applications/legion-brightness.desktop"
mkdir -p "$HOME/.local/share/applications"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Legion Brightness
Comment=Control Intel backlight brightness on Lenovo Legion laptops
Exec=$SCRIPT_DIR/brightness_applet.py
Icon=legion-brightness
Terminal=false
Categories=Utility;Settings;System;
Keywords=brightness;backlight;display;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"

echo "✓ Desktop entry created at:"
echo "  $DESKTOP_FILE"
echo ""

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Setup sudoers (required for passwordless brightness control):"
echo "   python3 setup_sudoers.py"
echo ""
echo "2. Launch the applet:"
echo "   • Run: python3 brightness_applet.py"
echo "   • Or search 'Legion Brightness' in your application menu"
echo "   • Or add it to your panel/dock"
echo ""
echo "The applet will appear in your application menu and can be"
echo "added to your system panel or dock for quick access."
echo ""

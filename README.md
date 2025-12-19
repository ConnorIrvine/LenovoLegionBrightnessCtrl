# Legion Brightness Control TLDR

I had been having a lot of backlight brightness issues on linux with my laptop and I realized that the issue has to do with nvidia optimus. Whether in nvidia performance or on demand mode, the brightness controls by default control the nvidia backlight. This does not work since the laptop routes its display through the igpu seemingly no matter what on linux (I have not figured out a way to setup advanced optimus)

This app has been quickly thrown together to make it more simple to run the brightnessctl commands required by the workaround I found (manually setting the intel backlight via the terminal). It uses GTK3 and provides a quick context menu with brightness options that I use frequently with the ability to open it up and set a manual brightness.

It should automatically detect your intel backlight maximum brightness but I have added the ability in settings to set it manually. Part of the install process will run a script that will setup passwordless operation using sudo. If you do not want to setup passwordless operations there is a setting to prompt a password with GUI every time if you so choose and you never have to run this script. The script does tell you exactly where the config is created for easy uninstall if you so choose.

I do not want to mess around with important files so I will not be programming an uninstaller until I get far more comfortable with linux.

Tested on Lenovo Legion 7i Gen 10 i9 14900HX with NVIDIA RTX 4070 with Linux Mint 22.2. Battery impact not tested yet.

## Features

- **System Tray Integration** - Sits in your notification area/system tray
- **Quick Presets** - Right-click menu with instant access to common brightness levels (20%, 40%, 50%, 60%, 80%, 100%)
- **Full Control Window** - Vertical slider for precise brightness adjustment (0-100%)
- **Passwordless Operation** - One-time setup eliminates password prompts
- **Persistent Settings** - Remembers your last brightness level across reboots
- **Auto-detection** - Automatically detects your Intel backlight maximum value during installation

## System Requirements

### Required Packages

- **brightnessctl** - Backend tool for controlling backlight devices with the terminal
- **Python 3** - Comes installed standard with linux. For convenience you may want to install the python is python3 package mentioned below
- **GTK3 Python bindings** (python3-gi) - For graphical interface. Should come standard
- **AppIndicator3** - For system tray integration
- **sudo** - For elevated permissions (configured once)

### Supported Systems

- Linux Mint (tested)
- Ubuntu/Debian-based distributions
- Any Linux distribution with GTK3 and system tray support theoretically

## Installation

### Step 1: Install Dependencies

**Linux Mint / Ubuntu / Debian:**
```bash
sudo apt install brightnessctl python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-appindicator3-0.1
```
Optional additional step for Mint users that I did for convenience:
```bash
sudo apt install python-is-python3
```


**Arch Linux:**
```bash
sudo pacman -S brightnessctl python-gobject gtk3 libappindicator-gtk3
```

**Fedora:**
```bash
sudo dnf install brightnessctl python3-gobject gtk3 libappindicator-gtk3
```

### Step 2: Clone This Repository

```bash
git clone https://github.com/yourusername/LenovoLegionBrightnessCtrl.git
cd LenovoLegionBrightnessCtrl
```

### Step 3: Run the Installer

Open a terminal window in the repository folder and run the following commands

```bash
chmod +x install.sh
./install.sh
```

The installer performs the following actions:
- Verifies all dependencies are installed
- Detects your Intel backlight maximum value automatically
- Creates configuration file at `~/.config/legion-brightness/config.json`
- Installs custom brightness icon
- Creates desktop entry for application menu access
- Makes all scripts executable

### Step 4: Configure Sudoers (Required)

Run the one-time sudoers configuration script:

```bash
python3 setup_sudoers.py
```

This script will:
- Prompt for your password once
- Install a sudoers rule to `/etc/sudoers.d/legion-brightness`
- Allow brightnessctl to run without password prompts
- Validate the configuration for safety

On subsequent runs, the script detects the existing configuration and reports that setup is complete.

## Usage

### Starting the Applet

The applet can be launched in several ways:

**From terminal:**
```bash
python3 brightness_applet.py
```

**From application menu:**
Search for "Legion Brightness" in your system's application launcher.

**Auto-start (optional):**
To launch automatically on login, manually add it to your list of startup applications

### Using the System Tray Icon

Once launched, the applet appears in your system tray/notification area:

**Right-click the tray icon to:**
- Set brightness to preset levels: 20%, 40%, 50%, 60%, 80%, or 100%
- Open the full control window
- Quit the application

**Click "Show Full Control" to open a window with:**
- Vertical slider for precise adjustment (0-100%)
- Current brightness percentage display
- Settings button to configure Intel backlight maximum
- Refresh button to reload current system brightness

The full control window appears in the bottom-right corner near the system tray.

## How It Works

### Brightness Control Mechanism

The applet controls your Intel backlight using the `brightnessctl` utility:

```bash
sudo brightnessctl --device=intel_backlight set X
```

Where `X` is the calculated brightness value based on:
- Your slider position (0-100%)
- Your Intel backlight's maximum value (typically 496)

For example, setting 50% brightness on a system with max value 496:
- Calculation: (50 / 100) * 496 = 248
- Command executed: `sudo brightnessctl --device=intel_backlight set 248`

### Passwordless Operation

The sudoers rule installed by `setup_sudoers.py` allows the brightnessctl command to run without password prompts. The rule is stored in `/etc/sudoers.d/legion-brightness` and is specific to your user account.

Example sudoers rule:
```
username ALL=(ALL) NOPASSWD: /usr/bin/brightnessctl --device=intel_backlight set *
username ALL=(ALL) NOPASSWD: /usr/bin/brightnessctl --device=intel_backlight get
```

## Configuration

Configuration file location: `~/.config/legion-brightness/config.json`

```json
{
  "intel_max": 496,
  "use_pkexec": false,
  "last_brightness": 50
}
```

### Configuration Parameters

- **intel_max**: Maximum brightness value for your Intel backlight device. This value is hardware-specific and is auto-detected during installation. Common values range from 400-1000.

- **use_pkexec**: Boolean flag for privilege escalation method:
  - `false` (default): Uses sudo with sudoers rule (no password prompts)
  - `true`: Uses pkexec (GUI password prompt each time)

- **last_brightness**: Percentage value (0-100) of the last set brightness level. This is automatically saved whenever you adjust brightness and restored when the applet starts.

### Manual Intel Maximum Detection

If you need to find your Intel backlight maximum value manually:

```bash
cat /sys/class/backlight/intel_backlight/max_brightness
```

You can also adjust this value in the applet's Settings dialog without editing the JSON file directly.

## Troubleshooting

### Brightness not changing or "Permission denied" errors

**Problem**: Clicking brightness options has no effect, or you see permission errors.

**Solution**: Ensure the sudoers rule is properly configured:

```bash
python3 setup_sudoers.py
```

Verify the sudoers rule is working:
```bash
sudo -n brightnessctl --device=intel_backlight get
```

This command should return a number immediately without prompting for a password. If it prompts for a password or fails, the sudoers rule is not configured correctly.

### System tray icon not appearing

**Problem**: The applet runs but no icon appears in the system tray.

**Solution**: Ensure AppIndicator3 is installed:

```bash
# Ubuntu/Debian/Mint
sudo apt install gir1.2-appindicator3-0.1

# Arch
sudo pacman -S libappindicator-gtk3
```

Some desktop environments may not support system tray indicators. Check your desktop environment's documentation for system tray support.

### Device not found errors

**Problem**: brightnessctl reports that the device doesn't exist.

**Solution**: List all available backlight devices:

```bash
brightnessctl --list
```

If your Intel backlight device has a different name than `intel_backlight`, edit the device name in [brightness_applet.py](brightness_applet.py). Search for `--device=intel_backlight` and replace it with your device's name.

### Applet fails to start

**Problem**: The applet crashes or shows import errors.

**Solution**: Verify all Python dependencies are installed:

```bash
python3 -c "import gi; gi.require_version('Gtk', '3.0'); gi.require_version('AppIndicator3', '0.1'); from gi.repository import Gtk, AppIndicator3; print('All dependencies OK')"
```

If this command fails, reinstall the GTK and AppIndicator packages listed in the installation section.

### Brightness resets after sleep/suspend

**Problem**: Brightness returns to a default value after waking from sleep.

**Solution**: The applet does not automatically restore brightness after system resume. You can either:
- Manually adjust brightness using the tray menu after wake
- Configure your system's power management to restore brightness levels
- The applet will restore your last setting when you next adjust brightness

## Any other issues

My fault

## Uninstallation

```bash
# Remove sudoers rule
sudo rm /etc/sudoers.d/legion-brightness

# Remove config directory
rm -rf ~/.config/legion-brightness

# Remove desktop entry
rm ~/.local/share/applications/legion-brightness.desktop

# Remove autostart entry (if added)
rm ~/.config/autostart/legion-brightness.desktop

# Remove the application directory
cd ..
rm -rf LenovoLegionBrightnessCtrl
```

## Repository Contents

- **brightness_applet.py** - Main application with system tray integration and GUI controls
- **setup_sudoers.py** - One-time sudoers configuration utility
- **install.sh** - Terminal installer
- **icon.svg** - Icon
- **README.md** - This document which hopefully can help you install and get everything set up easily!

## Technical Details

### Architecture

- **Language**: Python 3 (standard library with GTK bindings)
- **GUI Framework**: GTK3 via PyGObject (gi)
- **System Tray**: AppIndicator3 for cross-desktop compatibility
- **Privilege Escalation**: sudo with sudoers.d configuration
- **Backend**: brightnessctl utility for hardware control

## Compatibility Notes

This tool is designed for Intel integrated graphics backlight control. It has been tested on:
- Lenovo Legion 7i with Intel Tiger Lake graphics
- Linux Mint 20.x and 21.x

It should work on any Linux system with:
- Intel integrated graphics with backlight control
- A kernel that exposes `/sys/class/backlight/intel_backlight/`
- A desktop environment with system tray support

## Known Limitations

- Only controls Intel backlight (not external monitors)
- Requires brightnessctl to be installed (not pure Python)
- Needs sudo privileges (requires one-time sudoers setup)
- System tray support depends on desktop environment

Created for the Lenovo Legion 7i but should work on any Linux laptop with Intel backlight control (albeit most should work without issues)

This is likely a very overengineered solution. I am sure there is a simple fix but this works too.

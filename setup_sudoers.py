#!/usr/bin/env python3
"""
Legion Brightness - Sudoers Setup Utility
One-time setup to allow brightnessctl without password prompts
"""

import subprocess
import os
import sys
from pathlib import Path

SUDOERS_FILE = "/etc/sudoers.d/legion-brightness"
USERNAME = os.getenv("USER")

def check_sudoers_exists():
    """Check if sudoers rule is already configured"""
    if os.path.exists(SUDOERS_FILE):
        try:
            with open(SUDOERS_FILE, 'r') as f:
                content = f.read()
                # Check if it contains actual rules for this user
                if USERNAME in content and "brightnessctl" in content:
                    return True
        except PermissionError:
            # If we can't read it, assume it might exist and check differently
            pass
    return False

def test_sudo_access():
    """Test if brightnessctl already works without password"""
    try:
        result = subprocess.run(
            ["sudo", "-n", "brightnessctl", "--device=intel_backlight", "get"],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False

def create_sudoers_content():
    """Generate the sudoers file content"""
    return f"""# Sudoers rule for Legion Brightness Control
# Allows brightnessctl to run without password prompts
{USERNAME} ALL=(ALL) NOPASSWD: /usr/bin/brightnessctl --device=intel_backlight set *
{USERNAME} ALL=(ALL) NOPASSWD: /usr/bin/brightnessctl --device=intel_backlight get
"""

def install_sudoers_rule():
    """Install the sudoers rule with password prompt"""
    print("=" * 60)
    print("  Legion Brightness - Sudoers Setup")
    print("=" * 60)
    print()
    print("This will configure your system to allow brightness control")
    print("without password prompts.")
    print()
    print(f"User: {USERNAME}")
    print(f"Target file: {SUDOERS_FILE}")
    print()
    
    # Create temporary file with sudoers content
    temp_file = f"/tmp/legion-brightness-sudoers-{os.getpid()}"
    
    try:
        # Write content to temp file
        with open(temp_file, 'w') as f:
            f.write(create_sudoers_content())
        
        # Set proper permissions on temp file
        os.chmod(temp_file, 0o440)
        
        # Validate sudoers syntax
        print("Validating sudoers syntax...")
        result = subprocess.run(
            ["sudo", "visudo", "-c", "-f", temp_file],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"\nError: Invalid sudoers syntax")
            print(result.stderr)
            return False
        
        print("✓ Syntax valid")
        print()
        print("Installing sudoers rule...")
        print("(You will be prompted for your password)")
        print()
        
        # Copy to sudoers.d with sudo
        result = subprocess.run(
            ["sudo", "cp", temp_file, SUDOERS_FILE],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"\nError: Failed to install sudoers rule")
            print(result.stderr)
            return False
        
        # Ensure proper permissions
        subprocess.run(
            ["sudo", "chmod", "0440", SUDOERS_FILE],
            capture_output=True
        )
        
        print("✓ Sudoers rule installed successfully!")
        print()
        print("You can now run legion_brightness.py without password prompts.")
        print()
        
        return True
        
    except Exception as e:
        print(f"\nError: {e}")
        return False
    finally:
        # Clean up temp file
        try:
            os.remove(temp_file)
        except:
            pass

def main():
    print()
    
    # Check if already configured
    if test_sudo_access():
        print("=" * 60)
        print("  ✓ Sudoers Already Configured")
        print("=" * 60)
        print()
        print("Brightness control is already set up to work without")
        print("password prompts. No action needed!")
        print()
        return 0
    
    # Check if brightnessctl is installed
    if not os.path.exists("/usr/bin/brightnessctl"):
        print("=" * 60)
        print("  Error: brightnessctl Not Found")
        print("=" * 60)
        print()
        print("Please install brightnessctl first:")
        print("  Ubuntu/Debian: sudo apt install brightnessctl")
        print("  Arch: sudo pacman -S brightnessctl")
        print("  Fedora: sudo dnf install brightnessctl")
        print()
        return 1
    
    # Perform setup
    if install_sudoers_rule():
        # Verify it works
        print("Verifying setup...")
        if test_sudo_access():
            print("✓ Verification successful!")
            print()
            return 0
        else:
            print("⚠ Warning: Setup completed but verification failed.")
            print("You may need to log out and back in for changes to take effect.")
            print()
            return 0
    else:
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(1)

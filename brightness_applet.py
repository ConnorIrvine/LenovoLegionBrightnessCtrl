#!/usr/bin/env python3
"""
Lenovo Legion Brightness Control - GTK3 System Tray Applet
Simple vertical slider interface for brightness control with quick select values before opening the full applet.
"""

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, GLib, AppIndicator3
import subprocess
import json
from pathlib import Path

class BrightnessConfig:
    """Handle configuration loading and saving"""
    def __init__(self):
        self.config_file = Path.home() / ".config" / "legion-brightness" / "config.json"
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file or create default"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        default_config = {
            "intel_max": 496,
            "use_pkexec": False,
            "last_brightness": 50
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Save configuration to file"""
        if config:
            self.config = config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, indent=2, fp=f)
        except Exception as e:
            pass

class BrightnessController:
    """Handle brightness control operations"""
    def __init__(self, config):
        self.config = config
    
    def set_brightness(self, percentage):
        """Set brightness for Intel backlight"""
        intel_value = int((percentage / 100) * self.config['intel_max'])
        sudo_cmd = ["pkexec"] if self.config['use_pkexec'] else ["sudo"]
        
        try:
            cmd = sudo_cmd + ["brightnessctl", "--device=intel_backlight", "set", str(intel_value)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except Exception as e:
            return False
    
    def get_current_brightness(self):
        """Get current brightness from Intel backlight"""
        try:
            result = subprocess.run(["brightnessctl", "--device=intel_backlight", "get"],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                current = int(result.stdout.strip())
                percentage = int((current / self.config['intel_max']) * 100)
                return percentage
        except Exception as e:
            pass
        return None

class SettingsDialog(Gtk.Dialog):
    """Settings dialog"""
    
    def __init__(self, parent, config_manager, controller):
        super().__init__(title="Settings", parent=parent, modal=True)
        self.config_manager = config_manager
        self.controller = controller
        
        self.set_default_size(300, 150)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Intel max setting
        intel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        intel_label = Gtk.Label(label="Intel Max:")
        intel_label.set_width_chars(12)
        intel_label.set_xalign(0)
        intel_box.pack_start(intel_label, False, False, 0)
        
        self.intel_entry = Gtk.Entry()
        self.intel_entry.set_text(str(self.config_manager.config['intel_max']))
        intel_box.pack_start(self.intel_entry, True, True, 0)
        
        box.pack_start(intel_box, False, False, 0)
        
        # Pkexec checkbox
        self.pkexec_check = Gtk.CheckButton(label="Use pkexec (GUI password)")
        self.pkexec_check.set_active(self.config_manager.config['use_pkexec'])
        box.pack_start(self.pkexec_check, False, False, 0)
        
        help_label = Gtk.Label()
        help_label.set_markup("<small>Uncheck to use sudo\n(requires sudoers setup)</small>")
        help_label.set_xalign(0)
        box.pack_start(help_label, False, False, 0)
        
        self.show_all()
        
        # Connect OK button
        self.connect("response", self.on_response)
    
    def on_response(self, dialog, response):
        """Handle dialog response"""
        if response == Gtk.ResponseType.OK:
            try:
                intel_max = int(self.intel_entry.get_text())
                if intel_max > 0:
                    self.config_manager.config['intel_max'] = intel_max
                    self.config_manager.config['use_pkexec'] = self.pkexec_check.get_active()
                    self.config_manager.save_config()
            except ValueError:
                pass

class SystemTrayApplet:
    """System tray indicator for brightness control"""
    
    def __init__(self):
        self.config_manager = BrightnessConfig()
        self.controller = BrightnessController(self.config_manager.config)
        self.window = None
        self.updating_slider = False
        
        # Find icon path
        icon_path = Path(__file__).parent / "icon.svg"
        icon_name = str(icon_path) if icon_path.exists() else "legion-brightness"
        
        # Create indicator
        self.indicator = AppIndicator3.Indicator.new(
            "legion-brightness",
            icon_name,
            AppIndicator3.IndicatorCategory.HARDWARE
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        
        # Create menu
        menu = Gtk.Menu()
        
        # Quick brightness options
        for brightness in [100, 80, 60, 50, 40, 20]:
            item = Gtk.MenuItem(label=f"Set {brightness}%")
            item.connect("activate", self.set_quick_brightness, brightness)
            menu.append(item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Show window item
        show_item = Gtk.MenuItem(label="Show Full Control")
        show_item.connect("activate", self.show_window)
        menu.append(show_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        # Quit item
        quit_item = Gtk.MenuItem(label="Quit")
        quit_item.connect("activate", self.quit)
        menu.append(quit_item)
        
        menu.show_all()
        self.indicator.set_menu(menu)
        
    
    def set_quick_brightness(self, widget, brightness):
        """Set brightness quickly from menu"""
        self.controller.set_brightness(brightness)
        self.config_manager.config['last_brightness'] = brightness
        self.config_manager.save_config()
    
    def show_window(self, widget):
        """Show the brightness control window"""
        if self.window is None or not self.window.get_visible():
            self.window = BrightnessApplet(self)
            self.window.show_all()
            # Position window at bottom-right corner
            screen = self.window.get_screen()
            monitor = screen.get_monitor_at_point(screen.get_width() - 1, screen.get_height() - 1)
            geometry = screen.get_monitor_geometry(monitor)
            window_width, window_height = self.window.get_size()
            x = geometry.x + geometry.width - window_width - 10
            y = geometry.y + geometry.height - window_height - 40
            self.window.move(x, y)
        else:
            self.window.present()
    
    def on_window_closed(self):
        """Handle window close"""
        self.window = None
    
    def quit(self, widget):
        """Quit the application"""
        Gtk.main_quit()

class BrightnessApplet(Gtk.Window):
    """GTK3 GUI Window for brightness control"""
    
    def __init__(self, tray_applet):
        super().__init__(title="Legion Brightness")
        self.set_default_size(120, 400)
        self.set_resizable(False)
        self.tray_applet = tray_applet
        
        # Initialize config and controller from tray applet
        self.config_manager = tray_applet.config_manager
        self.controller = tray_applet.controller
        self.updating = False
        
        # Connect close event to hide instead of destroy
        self.connect("delete-event", self.on_close)
        
        # Create main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(15)
        vbox.set_margin_bottom(15)
        vbox.set_margin_start(15)
        vbox.set_margin_end(15)
        self.add(vbox)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b>☀ Brightness</b>")
        vbox.pack_start(title, False, False, 0)
        
        # Brightness percentage label
        self.brightness_label = Gtk.Label()
        self.brightness_label.set_markup("<span font='28' weight='bold'>50%</span>")
        vbox.pack_start(self.brightness_label, False, False, 5)
        
        # Vertical scale (slider)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.VERTICAL)
        self.scale.set_range(1, 100)
        self.scale.set_inverted(True)  # 100 at top, 1 at bottom
        self.scale.set_value(self.config_manager.config['last_brightness'])
        self.scale.set_digits(0)
        self.scale.set_value_pos(Gtk.PositionType.BOTTOM)
        self.scale.connect("value-changed", self.on_scale_changed)
        
        # Add marks at 25, 50, 75
        self.scale.add_mark(25, Gtk.PositionType.LEFT, "")
        self.scale.add_mark(50, Gtk.PositionType.LEFT, "")
        self.scale.add_mark(75, Gtk.PositionType.LEFT, "")
        
        vbox.pack_start(self.scale, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<small>Ready</small>")
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        vbox.pack_start(button_box, False, False, 5)
        
        # Settings button
        settings_btn = Gtk.Button(label="⚙")
        settings_btn.set_tooltip_text("Settings")
        settings_btn.connect("clicked", self.on_settings_clicked)
        button_box.pack_start(settings_btn, True, True, 0)
        
        # Refresh button
        refresh_btn = Gtk.Button(label="🔄")
        refresh_btn.set_tooltip_text("Refresh")
        refresh_btn.connect("clicked", self.on_refresh_clicked)
        button_box.pack_start(refresh_btn, True, True, 0)
        
        # Close button
        close_btn = Gtk.Button(label="✕")
        close_btn.set_tooltip_text("Close")
        close_btn.connect("clicked", self.on_close_clicked)
        button_box.pack_start(close_btn, True, True, 0)
        
        # Load current brightness
        self.load_current_brightness()
        
        # Timeout for debounced updates
        self.update_timeout = None
    
    def on_close(self, widget, event):
        """Handle window close - hide instead of destroy"""
        self.hide()
        self.tray_applet.on_window_closed()
        return True  # Prevent destroy
    
    def on_close_clicked(self, button):
        """Handle close button click"""
        self.hide()
        self.tray_applet.on_window_closed()
    
    def load_current_brightness(self):
        """Load current brightness on startup"""
        current = self.controller.get_current_brightness()
        if current is not None:
            self.updating = True
            self.scale.set_value(current)
            self.updating = False
            self.update_label(current)
    
    def update_label(self, value):
        """Update the brightness percentage label"""
        self.brightness_label.set_markup(f"<span font='28' weight='bold'>{int(value)}%</span>")
    
    def on_scale_changed(self, scale):
        """Handle slider value changes"""
        if self.updating:
            return
        
        value = int(scale.get_value())
        self.update_label(value)
        
        # Debounce: cancel previous timeout and set new one
        if self.update_timeout:
            GLib.source_remove(self.update_timeout)
        
        self.update_timeout = GLib.timeout_add(300, self.apply_brightness, value)
    
    def apply_brightness(self, value):
        """Apply brightness change (called after debounce)"""
        self.status_label.set_markup("<small><span foreground='blue'>Setting...</span></small>")
        
        success = self.controller.set_brightness(value)
        
        if success:
            self.status_label.set_markup("<small><span foreground='green'>✓ Set</span></small>")
            self.config_manager.config['last_brightness'] = value
            self.config_manager.save_config()
        else:
            self.status_label.set_markup("<small><span foreground='red'>✗ Failed</span></small>")
        
        # Clear status after 2 seconds
        GLib.timeout_add(2000, lambda: self.status_label.set_markup("<small>Ready</small>"))
        
        self.update_timeout = None
        return False
    
    def on_refresh_clicked(self, button):
        """Refresh current brightness"""
        self.load_current_brightness()
        self.status_label.set_markup("<small><span foreground='green'>✓ Refreshed</span></small>")
        GLib.timeout_add(1500, lambda: self.status_label.set_markup("<small>Ready</small>"))
    
    def on_settings_clicked(self, button):
        """Open settings dialog"""
        dialog = SettingsDialog(self, self.config_manager, self.controller)
        response = dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Reload controller config
            self.controller.config = self.config_manager.config
            self.status_label.set_markup("<small><span foreground='green'>✓ Saved</span></small>")
            GLib.timeout_add(1500, lambda: self.status_label.set_markup("<small>Ready</small>"))
        
        dialog.destroy()

class SettingsDialog(Gtk.Dialog):
    """Settings dialog"""
    
    def __init__(self, parent, config_manager, controller):
        super().__init__(title="Settings", parent=parent, modal=True)
        self.config_manager = config_manager
        self.controller = controller
        
        self.set_default_size(300, 150)
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        box = self.get_content_area()
        box.set_spacing(10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        
        # Intel max setting
        intel_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        intel_label = Gtk.Label(label="Intel Max:")
        intel_label.set_width_chars(12)
        intel_label.set_xalign(0)
        intel_box.pack_start(intel_label, False, False, 0)
        
        self.intel_entry = Gtk.Entry()
        self.intel_entry.set_text(str(self.config_manager.config['intel_max']))
        intel_box.pack_start(self.intel_entry, True, True, 0)
        
        box.pack_start(intel_box, False, False, 0)
        
        # Pkexec checkbox
        self.pkexec_check = Gtk.CheckButton(label="Use pkexec (GUI password)")
        self.pkexec_check.set_active(self.config_manager.config['use_pkexec'])
        box.pack_start(self.pkexec_check, False, False, 0)
        
        help_label = Gtk.Label()
        help_label.set_markup("<small>Uncheck to use sudo\n(requires sudoers setup)</small>")
        help_label.set_xalign(0)
        box.pack_start(help_label, False, False, 0)
        
        self.show_all()
        
        # Connect OK button
        self.connect("response", self.on_response)
    
    def on_response(self, dialog, response):
        """Handle dialog response"""
        if response == Gtk.ResponseType.OK:
            try:
                intel_max = int(self.intel_entry.get_text())
                if intel_max > 0:
                    self.config_manager.config['intel_max'] = intel_max
                    self.config_manager.config['use_pkexec'] = self.pkexec_check.get_active()
                    self.config_manager.save_config()
            except ValueError:
                pass

def main():
    tray = SystemTrayApplet()
    Gtk.main()

if __name__ == "__main__":
    main()
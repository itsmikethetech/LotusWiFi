import os
import subprocess
import asyncio
import json
import time
import tempfile
from typing import Dict, Optional

import decky

class Plugin:
    def __init__(self):
        self.script_process: Optional[asyncio.subprocess.Process] = None
        self.is_monitoring = False
        self.script_path = os.path.join(os.path.dirname(__file__), "wifitoggler")
        self.settings = {
            "max_latency": 100,
            "check_interval": 10,
            "ping_host": "8.8.8.8",
            "enabled": False
        }
        self.last_status = {
            "latency": 0,
            "status": "unknown",
            "timestamp": 0
        }
        self.restart_count = 0

    async def get_settings(self) -> Dict:
        """Get current plugin settings"""
        return self.settings

    async def update_settings(self, new_settings: Dict) -> bool:
        """Update plugin settings and restart script if running"""
        try:
            old_settings = self.settings.copy()
            self.settings.update(new_settings)
            await self._save_settings()
            
            # If monitoring and settings changed, restart the script
            if self.is_monitoring and (
                old_settings["max_latency"] != self.settings["max_latency"] or
                old_settings["check_interval"] != self.settings["check_interval"] or
                old_settings["ping_host"] != self.settings["ping_host"]
            ):
                await self.stop_monitoring()
                if self.settings["enabled"]:
                    await self.start_monitoring()
            
            return True
        except Exception as e:
            decky.logger.error(f"Failed to update settings: {e}")
            return False

    async def get_status(self) -> Dict:
        """Get current monitoring status"""
        return {
            "is_monitoring": self.is_monitoring,
            "last_ping": self.last_status,
            "restart_count": self.restart_count,
            "settings": self.settings
        }

    async def start_monitoring(self) -> bool:
        """Start the Wi-Fi monitoring script"""
        if self.is_monitoring:
            return True
            
        try:
            # Create a modified version of the script with current settings
            modified_script = await self._create_configured_script()
            
            # Start the script process
            self.script_process = await asyncio.create_subprocess_exec(
                "bash", modified_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.is_monitoring = True
            self.settings["enabled"] = True
            
            # Start monitoring the script output
            asyncio.create_task(self._monitor_script_output())
            
            decky.logger.info("Wi-Fi monitoring script started")
            await decky.emit("wifi_status_changed", {"monitoring": True})
            return True
            
        except Exception as e:
            decky.logger.error(f"Failed to start monitoring script: {e}")
            self.is_monitoring = False
            return False

    async def stop_monitoring(self) -> bool:
        """Stop the Wi-Fi monitoring script"""
        try:
            self.is_monitoring = False
            self.settings["enabled"] = False
            
            if self.script_process:
                # Send SIGTERM to gracefully stop the script
                self.script_process.terminate()
                try:
                    await asyncio.wait_for(self.script_process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if it doesn't stop gracefully
                    self.script_process.kill()
                    await self.script_process.wait()
                self.script_process = None
            
            decky.logger.info("Wi-Fi monitoring script stopped")
            await decky.emit("wifi_status_changed", {"monitoring": False})
            return True
            
        except Exception as e:
            decky.logger.error(f"Failed to stop monitoring script: {e}")
            return False

    async def _create_configured_script(self) -> str:
        """Create a temporary script file with current settings"""
        try:
            # Read the original script
            with open(self.script_path, 'r') as f:
                script_content = f.read()
            
            # Replace the configuration variables
            script_content = script_content.replace(
                'MAX_LATENCY=100', 
                f'MAX_LATENCY={self.settings["max_latency"]}'
            )
            script_content = script_content.replace(
                'CHECK_INTERVAL=10', 
                f'CHECK_INTERVAL={self.settings["check_interval"]}'
            )
            script_content = script_content.replace(
                'PING_HOST="8.8.8.8"', 
                f'PING_HOST="{self.settings["ping_host"]}"'
            )
            
            # Create temporary file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.sh', prefix='lotuswifi_')
            with os.fdopen(temp_fd, 'w') as temp_file:
                temp_file.write(script_content)
            
            # Make it executable
            os.chmod(temp_path, 0o755)
            
            return temp_path
            
        except Exception as e:
            decky.logger.error(f"Failed to create configured script: {e}")
            raise

    async def _monitor_script_output(self):
        """Monitor the script output for status updates"""
        if not self.script_process:
            return
            
        try:
            while self.is_monitoring and self.script_process:
                line = await self.script_process.stdout.readline()
                if not line:
                    break
                    
                line_str = line.decode().strip()
                decky.logger.info(f"Script output: {line_str}")
                
                # Parse the output for status information
                await self._parse_script_output(line_str)
                
        except Exception as e:
            decky.logger.error(f"Error monitoring script output: {e}")
        finally:
            if self.is_monitoring:
                self.is_monitoring = False
                await decky.emit("wifi_status_changed", {"monitoring": False})

    async def _parse_script_output(self, line: str):
        """Parse script output to extract status information"""
        try:
            current_time = int(time.time())
            
            if "Ping OK" in line:
                # Extract latency from "Ping OK (XXXms)" format
                import re
                match = re.search(r'Ping OK \((\d+(?:\.\d+)?)ms\)', line)
                if match:
                    latency = float(match.group(1))
                    self.last_status = {
                        "latency": latency,
                        "status": "ok",
                        "timestamp": current_time
                    }
                    await decky.emit("ping_result", self.last_status)
                    
            elif "High latency detected" in line:
                # Extract latency from "High latency detected (XXXms)" format
                import re
                match = re.search(r'High latency detected \((\d+(?:\.\d+)?)ms\)', line)
                if match:
                    latency = float(match.group(1))
                    self.last_status = {
                        "latency": latency,
                        "status": "high",
                        "timestamp": current_time
                    }
                    await decky.emit("ping_result", self.last_status)
                    
            elif "Restarting Wi-Fi" in line:
                self.restart_count += 1
                await decky.emit("wifi_restarted", {
                    "count": self.restart_count, 
                    "reason": f"High latency detected"
                })
                
            elif "Ping failed or timed out" in line:
                self.last_status = {
                    "latency": -1,
                    "status": "failed",  
                    "timestamp": current_time
                }
                await decky.emit("ping_result", self.last_status)
                
        except Exception as e:
            decky.logger.error(f"Error parsing script output: {e}")

    async def _load_settings(self):
        """Load settings from file"""
        try:
            settings_file = os.path.join(decky.DECKY_SETTINGS_DIR, "lotuswifi.json")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
        except Exception as e:
            decky.logger.error(f"Failed to load settings: {e}")

    async def _save_settings(self):
        """Save settings to file"""
        try:
            settings_file = os.path.join(decky.DECKY_SETTINGS_DIR, "lotuswifi.json")
            os.makedirs(decky.DECKY_SETTINGS_DIR, exist_ok=True)
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            decky.logger.error(f"Failed to save settings: {e}")

    async def _main(self):
        self.loop = asyncio.get_event_loop()
        decky.logger.info("LotusWiFi plugin loaded")
        
        # Make sure the script is executable
        if os.path.exists(self.script_path):
            os.chmod(self.script_path, 0o755)
        else:
            decky.logger.error(f"Script not found at {self.script_path}")
        
        await self._load_settings()
        
        # Start monitoring if it was enabled
        if self.settings.get("enabled", False):
            await self.start_monitoring()

    async def _unload(self):
        await self.stop_monitoring()
        await self._save_settings()
        decky.logger.info("LotusWiFi plugin unloaded")

    async def _uninstall(self):
        await self.stop_monitoring()
        decky.logger.info("LotusWiFi plugin uninstalled")

    async def _migration(self):
        decky.logger.info("LotusWiFi migration complete")

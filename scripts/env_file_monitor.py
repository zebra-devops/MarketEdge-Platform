#!/usr/bin/env python3
"""
Environment File Monitor
Monitors .env files for changes and automatically creates backups
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json


try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("Warning: watchdog not installed. File monitoring will use polling mode.")


@dataclass
class MonitoredFile:
    """Configuration for a monitored file"""
    path: str
    auto_backup: bool = True
    backup_on_change: bool = True
    validate_on_change: bool = True
    alert_on_placeholder: bool = True
    last_hash: str = ""
    last_modified: float = 0.0


class EnvFileEventHandler(FileSystemEventHandler):
    """Handles file system events for .env files"""
    
    def __init__(self, monitor):
        self.monitor = monitor
        super().__init__()
    
    def on_modified(self, event):
        if not event.is_directory:
            self.monitor.handle_file_change(event.src_path, "modified")
    
    def on_created(self, event):
        if not event.is_directory:
            self.monitor.handle_file_change(event.src_path, "created")
    
    def on_moved(self, event):
        if not event.is_directory:
            self.monitor.handle_file_change(event.dest_path, "moved")


class EnvFileMonitor:
    """Monitors environment files and provides automatic backup and validation"""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir or os.getcwd())
        self.monitored_files: Dict[str, MonitoredFile] = {}
        self.observers: List[Observer] = []
        self.running = False
        self.polling_thread = None
        self.polling_interval = 5.0  # seconds
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        log_file = self.root_dir / ".env_backups" / "monitor.log"
        log_file.parent.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)
        
        # Callbacks for events
        self.on_file_changed: List[Callable] = []
        self.on_backup_created: List[Callable] = []
        self.on_validation_failed: List[Callable] = []
        self.on_placeholder_detected: List[Callable] = []
        
        # Auto-discover .env files
        self.discover_env_files()
    
    def discover_env_files(self):
        """Automatically discover .env files to monitor"""
        env_patterns = [".env", ".env.local", ".env.production", ".env.development", ".env.staging"]
        
        for pattern in env_patterns:
            env_file = self.root_dir / pattern
            if env_file.exists():
                self.add_monitored_file(str(env_file))
        
        # Look in subdirectories (backend, frontend)
        for subdir in ["backend", "frontend"]:
            subdir_path = self.root_dir / subdir
            if subdir_path.exists():
                for pattern in env_patterns:
                    env_file = subdir_path / pattern
                    if env_file.exists():
                        self.add_monitored_file(str(env_file))
    
    def add_monitored_file(self, file_path: str, **kwargs):
        """Add a file to be monitored"""
        abs_path = str(Path(file_path).resolve())
        
        config = MonitoredFile(
            path=abs_path,
            **kwargs
        )
        
        # Initialize file hash and modification time
        if Path(abs_path).exists():
            config.last_hash = self._calculate_file_hash(abs_path)
            config.last_modified = Path(abs_path).stat().st_mtime
        
        self.monitored_files[abs_path] = config
        self.logger.info(f"Added monitored file: {abs_path}")
    
    def remove_monitored_file(self, file_path: str):
        """Remove a file from monitoring"""
        abs_path = str(Path(file_path).resolve())
        if abs_path in self.monitored_files:
            del self.monitored_files[abs_path]
            self.logger.info(f"Removed monitored file: {abs_path}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""
    
    def _parse_env_file(self, file_path: str) -> Dict[str, str]:
        """Parse environment file and return key-value pairs"""
        env_vars = {}
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            self.logger.error(f"Failed to parse env file {file_path}: {e}")
        
        return env_vars
    
    def _detect_placeholder_secrets(self, env_vars: Dict[str, str]) -> List[str]:
        """Detect placeholder values in critical secrets"""
        placeholder_patterns = [
            "your-auth0-client-secret",
            "your-super-secret-jwt-key",
            "your-auth0-domain",
            "your-auth0-client-id",
            "change-this-in-production",
            "placeholder",
            "replace-me",
            "todo",
            "example"
        ]
        
        critical_secrets = [
            "AUTH0_CLIENT_SECRET",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "REDIS_URL",
            "AUTH0_DOMAIN",
            "AUTH0_CLIENT_ID"
        ]
        
        placeholder_secrets = []
        
        for key, value in env_vars.items():
            if key in critical_secrets:
                value_lower = value.lower().strip('"\'')
                if any(pattern in value_lower for pattern in placeholder_patterns):
                    placeholder_secrets.append(key)
        
        return placeholder_secrets
    
    def handle_file_change(self, file_path: str, event_type: str):
        """Handle a file change event"""
        abs_path = str(Path(file_path).resolve())
        
        if abs_path not in self.monitored_files:
            # Check if this is an env file we should monitor
            if any(pattern in Path(file_path).name for pattern in [".env"]):
                self.add_monitored_file(abs_path)
            else:
                return
        
        config = self.monitored_files[abs_path]
        
        # Skip if file doesn't exist
        if not Path(abs_path).exists():
            return
        
        # Check if file actually changed
        current_hash = self._calculate_file_hash(abs_path)
        if current_hash == config.last_hash:
            return  # No actual change
        
        self.logger.info(f"File change detected: {abs_path} ({event_type})")
        
        # Create backup before processing
        if config.backup_on_change:
            self._create_backup(abs_path, f"file-{event_type}")
        
        # Validate the file
        if config.validate_on_change:
            self._validate_file(abs_path)
        
        # Update tracking information
        config.last_hash = current_hash
        config.last_modified = time.time()
        
        # Fire callbacks
        for callback in self.on_file_changed:
            try:
                callback(abs_path, event_type)
            except Exception as e:
                self.logger.error(f"File change callback failed: {e}")
    
    def _create_backup(self, file_path: str, reason: str):
        """Create a backup of the file"""
        try:
            # Import backup manager
            from env_backup_manager import EnvBackupManager
            
            backup_manager = EnvBackupManager(self.root_dir)
            backup_metadata = backup_manager.create_backup(
                file_path, 
                reason=reason, 
                environment=os.getenv("ENVIRONMENT", "development")
            )
            
            if backup_metadata:
                self.logger.info(f"Backup created: {backup_metadata.filename}")
                
                # Fire backup created callbacks
                for callback in self.on_backup_created:
                    try:
                        callback(file_path, backup_metadata.filename)
                    except Exception as e:
                        self.logger.error(f"Backup callback failed: {e}")
            else:
                self.logger.error(f"Failed to create backup for {file_path}")
        
        except Exception as e:
            self.logger.error(f"Backup creation failed for {file_path}: {e}")
    
    def _validate_file(self, file_path: str):
        """Validate environment file contents"""
        try:
            env_vars = self._parse_env_file(file_path)
            
            # Check for placeholder secrets
            placeholder_secrets = self._detect_placeholder_secrets(env_vars)
            if placeholder_secrets:
                self.logger.warning(f"Placeholder secrets detected in {file_path}: {placeholder_secrets}")
                
                # Fire placeholder detection callbacks
                for callback in self.on_placeholder_detected:
                    try:
                        callback(file_path, placeholder_secrets)
                    except Exception as e:
                        self.logger.error(f"Placeholder callback failed: {e}")
            
            # Additional validation using secret manager if available
            try:
                from app.core.secret_manager import secret_manager
                
                # Temporarily update environment with new values for validation
                original_env = {}
                for key, value in env_vars.items():
                    original_env[key] = os.getenv(key)
                    os.environ[key] = value
                
                # Clear secret manager cache and validate
                secret_manager.clear_cache()
                validation_summary = secret_manager.get_validation_summary()
                
                # Restore original environment
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
                
                if validation_summary["invalid_secrets"] > 0:
                    self.logger.error(f"Secret validation failed for {file_path}")
                    
                    # Fire validation failed callbacks
                    for callback in self.on_validation_failed:
                        try:
                            callback(file_path, validation_summary)
                        except Exception as e:
                            self.logger.error(f"Validation callback failed: {e}")
                else:
                    self.logger.info(f"Secret validation passed for {file_path}")
            
            except ImportError:
                self.logger.debug("Secret manager not available for validation")
                
        except Exception as e:
            self.logger.error(f"File validation failed for {file_path}: {e}")
    
    def start_monitoring(self):
        """Start monitoring files"""
        if self.running:
            self.logger.warning("Monitor is already running")
            return
        
        self.running = True
        self.logger.info("Starting environment file monitoring")
        
        if WATCHDOG_AVAILABLE:
            self._start_watchdog_monitoring()
        else:
            self._start_polling_monitoring()
    
    def stop_monitoring(self):
        """Stop monitoring files"""
        if not self.running:
            return
        
        self.running = False
        self.logger.info("Stopping environment file monitoring")
        
        # Stop watchdog observers
        for observer in self.observers:
            observer.stop()
            observer.join()
        self.observers.clear()
        
        # Stop polling thread
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=5)
    
    def _start_watchdog_monitoring(self):
        """Start watchdog-based file monitoring"""
        # Group files by directory to minimize observers
        directories = set()
        for file_path in self.monitored_files.keys():
            directories.add(str(Path(file_path).parent))
        
        for directory in directories:
            observer = Observer()
            event_handler = EnvFileEventHandler(self)
            observer.schedule(event_handler, directory, recursive=False)
            observer.start()
            self.observers.append(observer)
            self.logger.info(f"Started watching directory: {directory}")
    
    def _start_polling_monitoring(self):
        """Start polling-based file monitoring"""
        def polling_worker():
            while self.running:
                try:
                    self._check_files_polling()
                    time.sleep(self.polling_interval)
                except Exception as e:
                    self.logger.error(f"Polling worker error: {e}")
                    time.sleep(self.polling_interval)
        
        self.polling_thread = threading.Thread(target=polling_worker, daemon=True)
        self.polling_thread.start()
        self.logger.info("Started polling-based file monitoring")
    
    def _check_files_polling(self):
        """Check files for changes using polling"""
        for file_path, config in self.monitored_files.items():
            try:
                if not Path(file_path).exists():
                    continue
                
                current_mtime = Path(file_path).stat().st_mtime
                if current_mtime > config.last_modified:
                    self.handle_file_change(file_path, "modified")
            
            except Exception as e:
                self.logger.error(f"Error checking file {file_path}: {e}")
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        status = {
            "running": self.running,
            "monitoring_method": "watchdog" if WATCHDOG_AVAILABLE else "polling",
            "monitored_files": len(self.monitored_files),
            "files": []
        }
        
        for file_path, config in self.monitored_files.items():
            file_exists = Path(file_path).exists()
            status["files"].append({
                "path": file_path,
                "exists": file_exists,
                "auto_backup": config.auto_backup,
                "last_modified": config.last_modified,
                "last_hash": config.last_hash[:8] if config.last_hash else None
            })
        
        return status
    
    def manual_check(self):
        """Manually check all monitored files"""
        self.logger.info("Performing manual file check")
        
        for file_path in self.monitored_files.keys():
            if Path(file_path).exists():
                current_hash = self._calculate_file_hash(file_path)
                config = self.monitored_files[file_path]
                
                if current_hash != config.last_hash:
                    self.handle_file_change(file_path, "manual-check")
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add a callback for monitoring events"""
        if event_type == "file_changed":
            self.on_file_changed.append(callback)
        elif event_type == "backup_created":
            self.on_backup_created.append(callback)
        elif event_type == "validation_failed":
            self.on_validation_failed.append(callback)
        elif event_type == "placeholder_detected":
            self.on_placeholder_detected.append(callback)
        else:
            raise ValueError(f"Unknown event type: {event_type}")


def main():
    """Command line interface for the file monitor"""
    import argparse
    import signal
    
    parser = argparse.ArgumentParser(description="Environment File Monitor")
    parser.add_argument("--root-dir", default=".", help="Root directory to monitor")
    parser.add_argument("--interval", type=float, default=5.0, help="Polling interval in seconds")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    monitor = EnvFileMonitor(args.root_dir)
    monitor.polling_interval = args.interval
    
    # Add some example callbacks
    def on_file_changed(file_path, event_type):
        print(f"File changed: {file_path} ({event_type})")
    
    def on_placeholder_detected(file_path, placeholders):
        print(f"⚠️  Placeholder secrets detected in {file_path}: {placeholders}")
    
    monitor.add_callback("file_changed", on_file_changed)
    monitor.add_callback("placeholder_detected", on_placeholder_detected)
    
    # Handle shutdown gracefully
    def signal_handler(sig, frame):
        print("\nShutting down monitor...")
        monitor.stop_monitoring()
        exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        monitor.start_monitoring()
        
        if args.daemon:
            # Keep running as daemon
            while monitor.running:
                time.sleep(1)
        else:
            # Interactive mode
            print("Environment file monitor started. Press Ctrl+C to stop.")
            print(f"Monitoring {len(monitor.monitored_files)} files:")
            for file_path in monitor.monitored_files.keys():
                print(f"  - {file_path}")
            
            while monitor.running:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nShutting down monitor...")
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
#!/usr/bin/env python3

"""
Environment Variable Backup Manager
Prevents regressions like the Auth0 client secret incident
"""

import os
import shutil
import json
import hashlib
from datetime import datetime
from pathlib import Path
import argparse
import sys

class EnvBackupManager:
    def __init__(self, backup_dir=".env_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # Critical secrets that should never be placeholders
        self.critical_secrets = {
            'AUTH0_CLIENT_SECRET': ['your-auth0-client-secret', 'your_auth0_client_secret', 'placeholder'],
            'DATABASE_URL': ['postgresql://user:pass@localhost:5432/db', 'your-database-url'],
            'JWT_SECRET_KEY': ['your-jwt-secret', 'change-me', 'local-development-secret-key-change-in-production'],
            'REDIS_URL': ['redis://localhost:6379', 'your-redis-url']
        }
    
    def create_backup(self, env_file, reason="manual"):
        """Create a timestamped backup of the environment file"""
        if not Path(env_file).exists():
            print(f"❌ Error: {env_file} does not exist")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{Path(env_file).name}_{timestamp}.backup"
        backup_path = self.backup_dir / backup_filename
        
        try:
            # Copy the file
            shutil.copy2(env_file, backup_path)
            
            # Calculate hash for integrity
            file_hash = self._calculate_hash(env_file)
            
            # Create metadata
            metadata = {
                "timestamp": timestamp,
                "original_file": str(env_file),
                "reason": reason,
                "file_hash": file_hash,
                "backup_size": os.path.getsize(env_file),
                "created_at": datetime.now().isoformat()
            }
            
            # Save metadata
            metadata_path = backup_path.with_suffix('.backup.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Check for critical placeholder values
            warnings = self._check_placeholders(env_file)
            if warnings:
                metadata["warnings"] = warnings
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            print(f"✅ Backup created: {backup_filename}")
            if warnings:
                print("⚠️  WARNING: Placeholder values detected:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            # Cleanup old backups (keep last 50)
            self._cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    def list_backups(self):
        """List all available backups with metadata"""
        backup_files = list(self.backup_dir.glob("*.backup"))
        
        if not backup_files:
            print("📁 No backups found")
            return
        
        print(f"📋 Found {len(backup_files)} backup(s):\n")
        
        backups_with_metadata = []
        for backup_file in backup_files:
            metadata_file = backup_file.with_suffix('.backup.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                backups_with_metadata.append((backup_file, metadata))
        
        # Sort by timestamp (newest first)
        backups_with_metadata.sort(key=lambda x: x[1].get('created_at', ''), reverse=True)
        
        for backup_file, metadata in backups_with_metadata:
            timestamp = metadata.get('timestamp', 'unknown')
            reason = metadata.get('reason', 'unknown')
            size = metadata.get('backup_size', 0)
            warnings = metadata.get('warnings', [])
            
            print(f"📄 {backup_file.name}")
            print(f"   ⏰ Created: {timestamp}")
            print(f"   📝 Reason: {reason}")
            print(f"   📊 Size: {size} bytes")
            
            if warnings:
                print(f"   ⚠️  Warnings: {len(warnings)} issue(s)")
                for warning in warnings[:3]:  # Show first 3 warnings
                    print(f"      - {warning}")
                if len(warnings) > 3:
                    print(f"      ... and {len(warnings) - 3} more")
            
            print()
    
    def restore_backup(self, backup_file, target_file):
        """Restore a backup to the target file"""
        backup_path = self.backup_dir / backup_file
        
        if not backup_path.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return False
        
        try:
            # Create backup of current file before restoring
            if Path(target_file).exists():
                print("💾 Creating safety backup of current file...")
                self.create_backup(target_file, reason="pre-restore-safety")
            
            # Restore the backup
            shutil.copy2(backup_path, target_file)
            
            # Verify integrity if metadata exists
            metadata_file = backup_path.with_suffix('.backup.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Verify hash
                current_hash = self._calculate_hash(target_file)
                original_hash = metadata.get('file_hash')
                
                if current_hash == original_hash:
                    print(f"✅ Backup restored successfully: {target_file}")
                    print(f"🔍 Integrity verified (hash: {current_hash[:16]}...)")
                else:
                    print(f"⚠️  Backup restored but integrity check failed")
                    print(f"   Expected: {original_hash}")
                    print(f"   Got:      {current_hash}")
            else:
                print(f"✅ Backup restored: {target_file}")
                print("⚠️  No metadata found - could not verify integrity")
            
            # Check for placeholder values in restored file
            warnings = self._check_placeholders(target_file)
            if warnings:
                print("⚠️  WARNING: Restored file contains placeholder values:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error restoring backup: {e}")
            return False
    
    def _calculate_hash(self, file_path):
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _check_placeholders(self, env_file):
        """Check for placeholder values in critical secrets"""
        warnings = []
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
            
            for secret_name, placeholder_values in self.critical_secrets.items():
                for line in content.split('\n'):
                    if line.strip().startswith(f"{secret_name}="):
                        value = line.split('=', 1)[1].strip().strip('"\'')
                        
                        for placeholder in placeholder_values:
                            if placeholder.lower() in value.lower():
                                warnings.append(f"{secret_name} contains placeholder value: {placeholder}")
                                break
        
        except Exception as e:
            warnings.append(f"Could not validate file: {e}")
        
        return warnings
    
    def _cleanup_old_backups(self, keep_count=50):
        """Remove old backups, keeping only the most recent ones"""
        backup_files = list(self.backup_dir.glob("*.backup"))
        
        if len(backup_files) <= keep_count:
            return
        
        # Sort by modification time
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove oldest backups
        for backup_file in backup_files[keep_count:]:
            try:
                backup_file.unlink()
                # Also remove metadata file
                metadata_file = backup_file.with_suffix('.backup.json')
                if metadata_file.exists():
                    metadata_file.unlink()
                print(f"🗑️  Cleaned up old backup: {backup_file.name}")
            except Exception as e:
                print(f"⚠️  Could not cleanup {backup_file.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Environment Variable Backup Manager")
    parser.add_argument("command", choices=["backup", "list", "restore"], help="Command to execute")
    parser.add_argument("file", nargs="?", help="Environment file to backup or restore to")
    parser.add_argument("--reason", default="manual", help="Reason for backup")
    parser.add_argument("--backup-dir", default=".env_backups", help="Backup directory")
    
    args = parser.parse_args()
    
    manager = EnvBackupManager(args.backup_dir)
    
    if args.command == "backup":
        if not args.file:
            print("❌ Error: Please specify a file to backup")
            sys.exit(1)
        
        success = manager.create_backup(args.file, args.reason)
        sys.exit(0 if success else 1)
    
    elif args.command == "list":
        manager.list_backups()
    
    elif args.command == "restore":
        if not args.file:
            print("❌ Error: Please specify a backup file to restore")
            sys.exit(1)
        
        # If file doesn't contain .backup, assume it's a backup filename
        if not args.file.endswith('.backup'):
            print(f"❌ Error: {args.file} doesn't appear to be a backup file")
            print("Use 'list' command to see available backups")
            sys.exit(1)
        
        # Extract target file from backup filename
        backup_name = Path(args.file).name
        # Assuming format: original_TIMESTAMP.backup
        target_file = backup_name.split('_')[0]  # Get the original filename part
        
        success = manager.restore_backup(args.file, target_file)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
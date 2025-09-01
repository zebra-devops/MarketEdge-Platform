#!/usr/bin/env python3
"""
Safe Environment File Editor
Provides safe editing of .env files with automatic backup and validation
"""

import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import argparse


class SafeEnvEditor:
    """Safe editor for environment files with automatic backup and validation"""
    
    def __init__(self, root_dir: str = None):
        self.root_dir = Path(root_dir or os.getcwd())
    
    def edit_file(self, env_file: str, editor: str = None) -> bool:
        """Safely edit an environment file with backup and validation"""
        env_path = Path(env_file)
        
        if not env_path.exists():
            print(f"Error: Environment file not found: {env_file}")
            return False
        
        # Determine editor
        if not editor:
            editor = os.getenv('EDITOR', 'nano')  # Default to nano
        
        print(f"Safe editing: {env_path}")
        print(f"Using editor: {editor}")
        
        # Step 1: Create backup before editing
        print("\nStep 1: Creating backup...")
        if not self._create_backup(env_path, "pre-edit"):
            print("❌ Failed to create backup. Aborting edit.")
            return False
        
        # Step 2: Create temporary copy for editing
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.env', delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            
        try:
            # Copy original to temp file
            shutil.copy2(env_path, temp_path)
            
            # Step 3: Open editor
            print(f"\nStep 2: Opening editor ({editor})...")
            result = subprocess.run([editor, str(temp_path)])
            
            if result.returncode != 0:
                print("❌ Editor exited with error. Changes not saved.")
                return False
            
            # Step 4: Validate changes
            print("\nStep 3: Validating changes...")
            if not self._validate_changes(env_path, temp_path):
                response = input("Validation failed. Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    print("❌ Edit aborted due to validation failure.")
                    return False
            
            # Step 5: Apply changes
            print("\nStep 4: Applying changes...")
            shutil.copy2(temp_path, env_path)
            
            # Step 6: Final validation
            print("\nStep 5: Final validation...")
            if self._final_validation(env_path):
                print("✅ File edited successfully!")
                return True
            else:
                print("⚠️  File edited but validation warnings exist.")
                return True
                
        finally:
            # Cleanup temp file
            if temp_path.exists():
                temp_path.unlink()
    
    def _create_backup(self, env_path: Path, reason: str) -> bool:
        """Create backup using backup manager"""
        try:
            sys.path.append(str(self.root_dir / "scripts"))
            from env_backup_manager import EnvBackupManager
            
            backup_manager = EnvBackupManager(self.root_dir)
            metadata = backup_manager.create_backup(
                str(env_path), 
                reason=reason,
                environment=os.getenv("ENVIRONMENT", "development")
            )
            
            if metadata:
                print(f"✅ Backup created: {metadata.filename}")
                return True
            else:
                return False
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return False
    
    def _validate_changes(self, original_path: Path, temp_path: Path) -> bool:
        """Validate changes between original and temporary file"""
        try:
            # Parse both files
            original_vars = self._parse_env_file(original_path)
            temp_vars = self._parse_env_file(temp_path)
            
            # Show changes
            print("\nChanges detected:")
            
            # Added variables
            added = {k: v for k, v in temp_vars.items() if k not in original_vars}
            if added:
                print("  Added variables:")
                for k, v in added.items():
                    # Mask sensitive values
                    display_value = self._mask_sensitive_value(k, v)
                    print(f"    + {k}={display_value}")
            
            # Removed variables
            removed = {k: v for k, v in original_vars.items() if k not in temp_vars}
            if removed:
                print("  Removed variables:")
                for k, v in removed.items():
                    display_value = self._mask_sensitive_value(k, v)
                    print(f"    - {k}={display_value}")
            
            # Changed variables
            changed = {k: {"old": original_vars[k], "new": temp_vars[k]} 
                      for k in original_vars.keys() & temp_vars.keys() 
                      if original_vars[k] != temp_vars[k]}
            if changed:
                print("  Changed variables:")
                for k, changes in changed.items():
                    old_value = self._mask_sensitive_value(k, changes["old"])
                    new_value = self._mask_sensitive_value(k, changes["new"])
                    print(f"    ~ {k}: {old_value} -> {new_value}")
            
            if not (added or removed or changed):
                print("  No changes detected")
                return True
            
            # Check for placeholder values in critical secrets
            critical_secrets = ["AUTH0_CLIENT_SECRET", "JWT_SECRET_KEY", "DATABASE_URL", "REDIS_URL"]
            placeholder_patterns = ["your-", "change-this", "placeholder", "example"]
            
            validation_issues = []
            
            for key in critical_secrets:
                if key in temp_vars:
                    value = temp_vars[key].lower()
                    if any(pattern in value for pattern in placeholder_patterns):
                        validation_issues.append(f"❌ {key} contains placeholder value")
            
            # Check for missing critical secrets
            for key in critical_secrets:
                if key not in temp_vars and key in original_vars:
                    validation_issues.append(f"⚠️  Critical secret {key} was removed")
            
            if validation_issues:
                print("\nValidation Issues:")
                for issue in validation_issues:
                    print(f"  {issue}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def _final_validation(self, env_path: Path) -> bool:
        """Perform final validation using secret manager if available"""
        try:
            # Load environment variables from file temporarily
            env_vars = self._parse_env_file(env_path)
            
            # Save current environment
            original_env = {}
            for key, value in env_vars.items():
                original_env[key] = os.getenv(key)
                os.environ[key] = value
            
            try:
                # Try to use secret manager for validation
                sys.path.append(str(self.root_dir / "app"))
                from core.secret_manager import secret_manager
                
                secret_manager.clear_cache()
                summary = secret_manager.get_validation_summary()
                
                print(f"Secret validation results:")
                print(f"  Valid secrets: {summary['valid_secrets']}")
                print(f"  Invalid secrets: {summary['invalid_secrets']}")
                print(f"  Placeholder secrets: {summary['placeholder_secrets']}")
                
                if summary['invalid_secrets'] > 0 or summary['placeholder_secrets'] > 0:
                    print("Issues found:")
                    for key, result in summary['validation_details'].items():
                        if not result.is_valid or result.issues:
                            print(f"  - {key}: {', '.join(result.issues)}")
                    return False
                
                return True
                
            except ImportError:
                print("Secret manager not available for validation")
                return True
            
            finally:
                # Restore original environment
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        
        except Exception as e:
            print(f"Final validation error: {e}")
            return True  # Don't fail edit on validation errors
    
    def _parse_env_file(self, file_path: Path) -> dict:
        """Parse environment file"""
        env_vars = {}
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
        return env_vars
    
    def _mask_sensitive_value(self, key: str, value: str) -> str:
        """Mask sensitive values for display"""
        sensitive_keys = ["SECRET", "PASSWORD", "TOKEN", "KEY"]
        
        if any(sensitive in key.upper() for sensitive in sensitive_keys):
            if len(value) <= 8:
                return "*" * len(value)
            else:
                return value[:3] + "*" * (len(value) - 6) + value[-3:]
        
        return value
    
    def quick_set(self, env_file: str, key: str, value: str) -> bool:
        """Quickly set a single environment variable with backup"""
        env_path = Path(env_file)
        
        print(f"Setting {key} in {env_path}")
        
        # Create backup
        if not self._create_backup(env_path, f"quick-set-{key}"):
            print("❌ Failed to create backup")
            return False
        
        # Read current file
        lines = []
        key_found = False
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        # Update or add the key
        new_lines = []
        for line in lines:
            if line.strip() and not line.strip().startswith('#') and '=' in line:
                line_key = line.split('=', 1)[0].strip()
                if line_key == key:
                    new_lines.append(f"{key}={value}\n")
                    key_found = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        # Add new key if not found
        if not key_found:
            new_lines.append(f"{key}={value}\n")
        
        # Write file
        with open(env_path, 'w') as f:
            f.writelines(new_lines)
        
        print(f"✅ Successfully set {key}")
        
        # Validate
        return self._final_validation(env_path)


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(description="Safe Environment File Editor")
    parser.add_argument("env_file", help="Environment file to edit")
    parser.add_argument("--editor", help="Editor to use (default: $EDITOR or nano)")
    parser.add_argument("--root-dir", default=".", help="Root directory")
    parser.add_argument("--set", nargs=2, metavar=("KEY", "VALUE"), help="Quickly set a key-value pair")
    
    args = parser.parse_args()
    
    editor = SafeEnvEditor(args.root_dir)
    
    if args.set:
        key, value = args.set
        success = editor.quick_set(args.env_file, key, value)
    else:
        success = editor.edit_file(args.env_file, args.editor)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
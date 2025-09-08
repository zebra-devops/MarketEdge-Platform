# Emergency Rollback Procedure
## Created: 2025-09-02 12:07:49
## Backup Location: backup_critical_20250902_120749

### Pre-Migration Backup Contents
- `.git_root` - Main repository git directory (101M total backup)
- `.git_platform_wrapper` - Platform wrapper git directory
- `.git_backend` - Backend git directory 
- `.git_frontend` - Frontend git directory
- `.git_mcp_vercel` - MCP Vercel git directory
- `git_status_*.txt` - Git status snapshots from all repos

### Critical Recovery Commands

#### 1. Full Repository Rollback
```bash
cd /Users/matt/Sites/MarketEdge
# Stop any running processes first
# Remove current .git directories
rm -rf .git platform-wrapper/.git platform-wrapper/backend/.git platform-wrapper/frontend/.git platform-wrapper/mcp-vercel/.git

# Restore all git directories
cp -r backup_critical_20250902_120749/.git_root .git
cp -r backup_critical_20250902_120749/.git_platform_wrapper platform-wrapper/.git
cp -r backup_critical_20250902_120749/.git_backend platform-wrapper/backend/.git
cp -r backup_critical_20250902_120749/.git_frontend platform-wrapper/frontend/.git
cp -r backup_critical_20250902_120749/.git_mcp_vercel platform-wrapper/mcp-vercel/.git

# Verify restoration
git status
cd platform-wrapper && git status
cd backend && git status
cd ../frontend && git status
cd ../mcp-vercel && git status
```

#### 2. Selective Rollback (if only specific repos affected)
```bash
# For main repo only
cp -r backup_critical_20250902_120749/.git_root .git

# For platform-wrapper only
cp -r backup_critical_20250902_120749/.git_platform_wrapper platform-wrapper/.git

# For backend only
cp -r backup_critical_20250902_120749/.git_backend platform-wrapper/backend/.git

# For frontend only
cp -r backup_critical_20250902_120749/.git_frontend platform-wrapper/frontend/.git

# For mcp-vercel only
cp -r backup_critical_20250902_120749/.git_mcp_vercel platform-wrapper/mcp-vercel/.git
```

### Pre-Cleanup Repository State
- **Main repository**: Modified files, see git_status_main.txt
- **Platform wrapper**: Up to date with origin/main, untracked files
- **Backend**: Missing render.yaml file
- **Frontend**: On epic-2-render-migration branch with extensive modifications
- **MCP Vercel**: Clean working tree

### Verification Steps
1. Check git status matches backed up status files
2. Verify all branches are preserved
3. Confirm no data loss in any repository
4. Test that all git operations work correctly

### Emergency Contact
If rollback fails, all git histories are preserved in this backup directory.
Original file structures remain intact until cleanup is confirmed successful.
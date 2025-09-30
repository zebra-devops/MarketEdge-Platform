# MarketEdge Development Guide

## Avoiding Project Conflicts

This project includes safe development practices to prevent conflicts with other local development projects (like your Zebra site on port 3001).

### Problem
When running multiple Next.js projects locally, they can interfere with each other when using commands like:
- `pkill -f "npm run dev"` (kills ALL npm dev processes)
- `lsof -ti :3000 | xargs kill -9` (can affect other projects)

### Solution: Use Isolated Development Commands

#### Port Allocation
- **MarketEdge Frontend**: Port 3000 (platform-wrapper/frontend)
- **MarketEdge Backend**: Port 8000 (FastAPI server)
- **Your Zebra Site**: Port 3001 (no conflict)
- **Other projects**: Ports 3002+ available

#### Starting MarketEdge Development Environment

##### Backend (Port 8000)
```bash
# From MarketEdge root directory
cd /Users/matt/Sites/MarketEdge
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

##### Frontend (Port 3000)
```bash
# From MarketEdge frontend directory
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
npm run dev
```

#### Safe Development Scripts (Recommended)

Create these scripts in the MarketEdge root to avoid conflicts:

**Create `dev-backend.sh`:**
```bash
#!/bin/bash
cd /Users/matt/Sites/MarketEdge
source venv/bin/activate
echo "Starting MarketEdge Backend on port 8000..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
echo $! > .backend-server.pid
echo "Backend PID: $(cat .backend-server.pid)"
wait
```

**Create `dev-frontend.sh`:**
```bash
#!/bin/bash
cd /Users/matt/Sites/MarketEdge/platform-wrapper/frontend
echo "Starting MarketEdge Frontend on port 3000..."
npm run dev -- --port 3000 &
echo $! > .frontend-server.pid
echo "Frontend PID: $(cat .frontend-server.pid)"
wait
```

**Create `stop.sh`:**
```bash
#!/bin/bash
echo "Stopping MarketEdge servers..."

# Stop backend
if [ -f .backend-server.pid ]; then
    kill $(cat .backend-server.pid) 2>/dev/null
    rm .backend-server.pid
    echo "Backend server stopped"
fi

# Stop frontend
if [ -f platform-wrapper/frontend/.frontend-server.pid ]; then
    kill $(cat platform-wrapper/frontend/.frontend-server.pid) 2>/dev/null
    rm platform-wrapper/frontend/.frontend-server.pid
    echo "Frontend server stopped"
fi

# Fallback: stop by port (MarketEdge only)
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "Cleaned up port 8000"
lsof -ti:3000 | xargs kill -9 2>/dev/null && echo "Cleaned up port 3000"
```

#### Make Scripts Executable
```bash
chmod +x dev-backend.sh dev-frontend.sh stop.sh
```

### Package.json Scripts (Alternative)

Add these to your `platform-wrapper/frontend/package.json`:

```json
{
  "scripts": {
    "dev": "next dev --port 3000",
    "dev:safe": "next dev --port 3000",
    "dev:stop": "../../stop.sh"
  }
}
```

### Current Server Status Check

```bash
# Check what's running on MarketEdge ports
lsof -i :3000,8000 | grep LISTEN

# Check all development servers
ps aux | grep -E "(next|uvicorn|npm)" | grep -v grep
```

### Multi-Project Port Map

| Project | Frontend Port | Backend Port | Status |
|---------|---------------|--------------|--------|
| MarketEdge | 3000 | 8000 | This project |
| Zebra Site | 3001 | N/A | Your other project |
| Available | 3002+ | 8001+ | Future projects |

### Best Practices

1. **Always use dedicated ports**: MarketEdge on 3000/8000, Zebra on 3001
2. **Use project-specific commands**: Avoid global kill commands
3. **Check before starting**: `lsof -i :3000,8000` to verify ports are free
4. **Proper shutdown**: Use project-specific stop scripts or Ctrl+C

### Database Development

```bash
# Reset database (if needed)
cd /Users/matt/Sites/MarketEdge/scripts/dev
./reset-db.sh

# Check migration status
alembic current
alembic upgrade head
```

### Environment Variables

Create `.env.local` in `platform-wrapper/frontend/`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NODE_ENV=development
```

### Troubleshooting

#### Port Conflicts
```bash
# Check what's using your ports
lsof -i :3000    # MarketEdge frontend
lsof -i :8000    # MarketEdge backend
lsof -i :3001    # Zebra site

# Kill specific processes (if needed)
kill $(lsof -ti:3000)  # Only kills port 3000
kill $(lsof -ti:8000)  # Only kills port 8000
```

#### Server Won't Start
```bash
# Clean up PIDs
rm -f .backend-server.pid platform-wrapper/frontend/.frontend-server.pid

# Check Node processes
ps aux | grep node | grep -v grep
```

#### Authentication Issues (401 Errors)
The Causal Edge API requires:
1. Valid authentication token in localStorage (dev) or cookies (prod)
2. User must have `CAUSAL_EDGE` application access
3. Feature flag `causal_edge_enabled` must be enabled

Check browser console for detailed debug logs.

### Quick Start Commands

```bash
# Start both servers (separate terminals)
Terminal 1: ./dev-backend.sh
Terminal 2: ./dev-frontend.sh

# Or manually:
Terminal 1: source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Terminal 2: cd platform-wrapper/frontend && npm run dev

# Stop everything
./stop.sh
```

This ensures MarketEdge runs on its dedicated ports (3000/8000) without interfering with your Zebra site on port 3001.
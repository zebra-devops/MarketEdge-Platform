"""
Production-ready Gunicorn configuration for MarketEdge platform
Optimized for Render deployment with proper error handling
"""

import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 1000

# Timeout configurations - CRITICAL for Render boot success
timeout = 120  # Increased from default 30s for complex startup
keepalive = 5
graceful_timeout = 30

# Process management
preload_app = False  # CRITICAL: Disable preloading to prevent boot issues
daemon = False
pidfile = None
tmp_upload_dir = None

# Logging
loglevel = os.getenv("LOG_LEVEL", "info").lower()
errorlog = "-"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Security
user = None
group = None
umask = 0

# Performance tuning
worker_tmp_dir = "/dev/shm" if os.path.exists("/dev/shm") else "/tmp"
max_requests_jitter = 50

# SSL (disabled for Render - handled by proxy)
keyfile = None
certfile = None

# Application settings (environment-aware paths)
import os
if os.getenv("RENDER") or os.path.exists("/app"):
    pythonpath = "/app"
    chdir = "/app"
else:
    pythonpath = "."
    chdir = "."

# CRITICAL: Startup validation function
def on_starting(server):
    """Called just before the master process is initialized."""
    print("🚀 Gunicorn master process starting...")
    print(f"Workers: {workers}")
    print(f"Worker class: {worker_class}")
    print(f"Bind: {bind}")
    print(f"Timeout: {timeout}s")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("🔄 Gunicorn reloading workers...")

def when_ready(server):
    """Called just after the server is started."""
    print("✅ Gunicorn server ready - all workers started successfully")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"⚠️  Worker {worker.pid} received interrupt signal")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    print(f"🔧 Forking worker {worker.age}...")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"✅ Worker {worker.pid} forked successfully")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    print(f"🎯 Worker {worker.pid} initialized application successfully")

def worker_abort(worker):
    """Called when a worker receives a SIGABRT signal."""
    print(f"❌ Worker {worker.pid} aborted!")
    
def on_exit(server):
    """Called just before exiting."""
    print("👋 Gunicorn server shutting down...")

# Environment-specific overrides
environment = os.getenv("ENVIRONMENT", "production").lower()

if environment == "development":
    workers = 1
    loglevel = "debug"
    reload = True
    print("🔧 Development mode: Single worker with reload enabled")

elif environment == "production":
    # Production optimizations
    preload_app = False  # Keep disabled for Render stability
    max_requests = 5000
    max_requests_jitter = 100
    print("🏭 Production mode: Multi-worker with stability optimizations")

# Memory management for Render
if os.getenv("RENDER"):
    # Render-specific optimizations
    workers = min(2, workers)  # Limit workers for Render memory constraints
    max_requests = 2000  # More frequent worker recycling
    timeout = 180  # Extended timeout for Render cold starts
    print(f"☁️  Render deployment detected: Optimized for {workers} workers")
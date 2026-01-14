"""
Run script for Crypto AI Backend
Can be executed from the project root directory
"""
import os
import sys
import subprocess

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
os.chdir(backend_dir)

# Add backend to path
sys.path.insert(0, backend_dir)

print("=" * 50)
print("  Crypto AI Backend Server")
print("=" * 50)
print(f"Working directory: {os.getcwd()}")
print()

# Initialize Database
print("[1/2] Initializing Database...")
from db import init_db
init_db()
print("      ✓ Database ready")
print()

# Start Server
print("[2/2] Starting FastAPI Server...")
print("      URL: http://127.0.0.1:8000")
print("      Docs: http://127.0.0.1:8000/docs")
print("=" * 50)

subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"])

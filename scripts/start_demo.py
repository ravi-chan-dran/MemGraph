#!/usr/bin/env python3
"""Demo startup script for MemoryGraph."""

import subprocess
import time
import sys
import os
import signal
import requests
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_service(port, name, max_retries=30):
    """Check if a service is running on the given port."""
    for i in range(max_retries):
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=2)
            if response.status_code == 200:
                print(f"✅ {name} is running on port {port}")
                return True
        except:
            pass
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"⏳ Waiting for {name} to start... ({i}/{max_retries})")
    return False

def start_service(command, name, port=None):
    """Start a service in the background."""
    print(f"🚀 Starting {name}...")
    try:
        # Activate virtual environment if it exists
        venv_python = project_root / ".venv" / "bin" / "python"
        if venv_python.exists():
            command = f"source {project_root}/.venv/bin/activate && {command}"
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        
        if port:
            if check_service(port, name):
                return process
            else:
                print(f"❌ Failed to start {name}")
                process.terminate()
                return None
        else:
            time.sleep(2)  # Give it time to start
            return process
    except Exception as e:
        print(f"❌ Error starting {name}: {e}")
        return None

def main():
    """Start the demo environment."""
    print("🎬 Starting MemoryGraph Demo Environment")
    print("=" * 50)
    
    processes = []
    
    try:
        # Change to project directory
        os.chdir(project_root)
        
        # 1. Start API Server
        api_process = start_service("python -m uvicorn app.api.routes:app --host 0.0.0.0 --port 8000", "API Server", 8000)
        if api_process:
            processes.append(("API Server", api_process))
        
        # 2. Start MCP Server
        mcp_process = start_service("python mcp_server.py", "MCP Server", 8002)
        if mcp_process:
            processes.append(("MCP Server", mcp_process))
        
        # 3. Start A/B Relay
        relay_process = start_service("python ab_relay.py", "A/B Relay", 8001)
        if relay_process:
            processes.append(("A/B Relay", relay_process))
        
        # 4. Check if seeding is needed
        print("🔍 Checking if demo data needs seeding...")
        try:
            # Check if data already exists by querying the API
            response = requests.get("http://localhost:8000/memory/facts?guid=plan_sponsor_acme", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("count", 0) > 0:
                    print("✅ Demo data already exists, skipping seeding")
                else:
                    print("🌱 No demo data found, seeding...")
                    result = subprocess.run([sys.executable, "scripts/seed_demo.py"], 
                                          capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        print("✅ Demo data seeded successfully")
                        if result.stdout:
                            print("Seeding output:", result.stdout[-200:])
                    else:
                        print(f"❌ Error seeding data: {result.stderr}")
            else:
                print("🌱 API not ready, seeding anyway...")
                result = subprocess.run([sys.executable, "scripts/seed_demo.py"], 
                                      capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    print("✅ Demo data seeded successfully")
                else:
                    print(f"❌ Error seeding data: {result.stderr}")
        except Exception as e:
            print(f"⚠️  Could not check existing data, seeding anyway: {e}")
            try:
                result = subprocess.run([sys.executable, "scripts/seed_demo.py"], 
                                      capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    print("✅ Demo data seeded successfully")
                else:
                    print(f"❌ Error seeding data: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("❌ Timeout seeding demo data (120s)")
            except Exception as seed_error:
                print(f"❌ Error seeding data: {seed_error}")
        
        # 5. Start Streamlit UI
        print("🖥️  Starting Streamlit UI...")
        ui_process = subprocess.Popen(
            ["streamlit", "run", "ui/streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
        processes.append(("Streamlit UI", ui_process))
        
        print("\n🎉 Demo Environment Started Successfully!")
        print("=" * 50)
        print("📱 Access Points:")
        print("  • Streamlit UI: http://localhost:8501")
        print("  • API Docs: http://localhost:8000/docs")
        print("  • A/B Relay: http://localhost:8001")
        print("  • MCP Server: http://localhost:8002")
        print("  • Neo4j Browser: http://localhost:7474")
        print("\n🧪 A/B Test Scenarios:")
        print("  1. Ask: 'What is the match formula?'")
        print("  2. Ask: 'When is payroll processed?'")
        print("  3. Ask: 'What is the auto-enrollment rate?'")
        print("  4. Ask: 'When are employee communications?'")
        print("  5. Toggle Memory ON/OFF to see the difference")
        print("\n⏹️  Press Ctrl+C to stop all services")
        
        # Wait for user interrupt
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down demo environment...")
            
    except Exception as e:
        print(f"❌ Error starting demo: {e}")
    
    finally:
        # Clean up processes
        for name, process in processes:
            try:
                print(f"🛑 Stopping {name}...")
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Integrated System Startup Script
Runs both backend Flask API and frontend Next.js development server
"""

import os
import sys
import subprocess
import threading
import time
import signal
from pathlib import Path

class IntegratedSystemManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.frontend_dir = self.project_root / "frontend"
        self.processes = []
        self.running = True

    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        try:
            import flask
            import flask_cors
            import pymongo
            import pandas
            print("✅ Python dependencies OK")
        except ImportError as e:
            print(f"❌ Missing Python dependency: {e}")
            print("Run: pip install flask flask-cors pymongo pandas plotly")
            return False
        
        # Check Node.js and npm
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js {result.stdout.strip()}")
            else:
                print("❌ Node.js not found")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found")
            return False
        
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm {result.stdout.strip()}")
            else:
                print("❌ npm not found")
                return False
        except FileNotFoundError:
            print("❌ npm not found")
            return False
        
        return True

    def install_frontend_dependencies(self):
        """Install frontend dependencies if needed"""
        print("📦 Checking frontend dependencies...")
        
        package_json = self.frontend_dir / "package.json"
        node_modules = self.frontend_dir / "node_modules"
        
        if not package_json.exists():
            print("❌ package.json not found in frontend directory")
            return False
        
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                result = subprocess.run(
                    ['npm', 'install'], 
                    cwd=self.frontend_dir,
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    print("✅ Frontend dependencies installed")
                else:
                    print(f"❌ Failed to install frontend dependencies: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                print("❌ Frontend dependency installation timed out")
                return False
            except Exception as e:
                print(f"❌ Error installing frontend dependencies: {e}")
                return False
        else:
            print("✅ Frontend dependencies already installed")
        
        return True

    def start_backend(self):
        """Start the Flask backend server"""
        print("🚀 Starting Flask backend server...")
        
        env = os.environ.copy()
        env['PYTHONPATH'] = str(self.project_root)
        
        try:
            process = subprocess.Popen(
                [sys.executable, 'app.py'],
                cwd=self.project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            def output_reader():
                for line in iter(process.stdout.readline, ''):
                    if not self.running:
                        break
                    print(f"🔧 Backend: {line.strip()}")
            
            output_thread = threading.Thread(target=output_reader, daemon=True)
            output_thread.start()
            
            self.processes.append(('backend', process))
            print("✅ Backend server started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False

    def start_frontend(self):
        """Start the Next.js frontend development server"""
        print("🎨 Starting Next.js frontend server...")
        
        try:
            process = subprocess.Popen(
                ['npm', 'run', 'dev'],
                cwd=self.frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            def output_reader():
                for line in iter(process.stdout.readline, ''):
                    if not self.running:
                        break
                    print(f"🎨 Frontend: {line.strip()}")
            
            output_thread = threading.Thread(target=output_reader, daemon=True)
            output_thread.start()
            
            self.processes.append(('frontend', process))
            print("✅ Frontend server started")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False

    def wait_for_servers(self):
        """Wait for servers to be ready"""
        print("⏳ Waiting for servers to be ready...")
        
        # Wait a bit for servers to start
        time.sleep(5)
        
        # Check backend
        try:
            import requests
            response = requests.get('http://localhost:8001/api/telemetry', timeout=5)
            if response.status_code == 200:
                print("✅ Backend API is responding")
            else:
                print(f"⚠️ Backend API returned status {response.status_code}")
        except:
            print("⚠️ Backend API not yet responding (this may be normal if no data)")
        
        # Check frontend
        try:
            import requests
            response = requests.get('http://localhost:5173', timeout=5)
            if response.status_code == 200:
                print("✅ Frontend is responding")
            else:
                print(f"⚠️ Frontend returned status {response.status_code}")
        except:
            print("⚠️ Frontend not yet responding")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.running = False
        self.shutdown()

    def shutdown(self):
        """Shutdown all processes"""
        print("🛑 Shutting down servers...")
        
        for name, process in self.processes:
            try:
                print(f"🛑 Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Force killing {name}...")
                process.kill()
                process.wait()
            except Exception as e:
                print(f"❌ Error stopping {name}: {e}")

    def run(self):
        """Run the integrated system"""
        print("🚀 Starting Integrated Predictive Maintenance System")
        print("=" * 60)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Install frontend dependencies
        if not self.install_frontend_dependencies():
            return False
        
        # Start backend
        if not self.start_backend():
            return False
        
        # Start frontend
        if not self.start_frontend():
            self.shutdown()
            return False
        
        # Wait for servers
        self.wait_for_servers()
        
        print("\n" + "=" * 60)
        print("🎉 Integrated System is Running!")
        print("📊 Frontend Dashboard: http://localhost:5173")
        print("🔧 Backend API: http://localhost:8001")
        print("📖 API Docs: http://localhost:8001/api/telemetry")
        print("\nPress Ctrl+C to stop all servers")
        print("=" * 60)
        
        # Keep running
        try:
            while self.running:
                time.sleep(1)
                
                # Check if any process died
                for name, process in self.processes:
                    if process.poll() is not None:
                        print(f"❌ {name} process died unexpectedly")
                        self.running = False
                        break
                        
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()
        
        return True

def main():
    """Main entry point"""
    manager = IntegratedSystemManager()
    success = manager.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Startup script for the Hexagonal Dungeon Crawler with highscore service
"""

import subprocess
import time
import sys
import os
import signal
import threading
from game.highscore_client import highscore_client

def start_highscore_service():
    """Start the highscore service in background"""
    print("🚀 Starting highscore service...")
    try:
        # Start the service as a subprocess
        service_process = subprocess.Popen([
            sys.executable, "highscore_service.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for service to start
        time.sleep(2)
        
        # Check if service is running
        if highscore_client.is_service_available():
            print("✅ Highscore service is running!")
            return service_process
        else:
            print("❌ Failed to start highscore service")
            return None
            
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        return None

def main():
    """Main startup function"""
    print("🎮 Hexagonal Dungeon Crawler Launcher")
    print("=" * 50)
    
    # Start highscore service
    service_process = start_highscore_service()
    
    try:
        # Start the game
        print("🎯 Starting game...")
        import main
        main.main()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    except Exception as e:
        print(f"❌ Game error: {e}")
    finally:
        # Clean up service process
        if service_process:
            print("🔄 Stopping highscore service...")
            service_process.terminate()
            try:
                service_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                service_process.kill()
            print("✅ Service stopped")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple script to check if the SteadwellOS application is up and running.
This doesn't require external dependencies like selenium or webdriver.
"""

import urllib.request
import urllib.error
import time
import sys
import socket
import subprocess
import os

def check_if_port_in_use(port, host='localhost'):
    """Check if the specified port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0

def get_http_status(url):
    """Get HTTP status code for a URL"""
    try:
        conn = urllib.request.urlopen(url, timeout=5)
        return conn.getcode()
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, socket.timeout):
        return None

def check_app_running(base_url="http://0.0.0.0:8080"):
    """Check if the application is running"""
    print(f"Checking if the application is running at {base_url}...")
    
    # Extract port from the URL
    if ":" in base_url.split("/")[2]:
        port = int(base_url.split("/")[2].split(":")[1])
    else:
        port = 80
    
    # Check if the port is in use
    if not check_if_port_in_use(port):
        print(f"❌ Port {port} is not in use. Application doesn't appear to be running.")
        return False
    
    # Check if the application responds
    status = get_http_status(base_url)
    if status is None:
        print(f"❌ Application at {base_url} is not responding.")
        return False
    
    print(f"✅ Application responded with HTTP status: {status}")
    
    # Check if login page is accessible
    login_url = f"{base_url}/login"
    login_status = get_http_status(login_url)
    if login_status in [200, 301, 302]:
        print(f"✅ Login page is accessible (status: {login_status})")
    else:
        print(f"❌ Login page is not accessible (status: {login_status})")
        return False
    
    # Check a few other key pages
    pages = [
        "/protocols",
        "/patients",
        "/dashboard"
    ]
    
    all_pages_ok = True
    for page in pages:
        page_url = f"{base_url}{page}"
        page_status = get_http_status(page_url)
        if page_status in [200, 301, 302]:
            print(f"✅ {page} page is accessible (status: {page_status})")
        else:
            print(f"❌ {page} page is not accessible (status: {page_status})")
            all_pages_ok = False
    
    if all_pages_ok:
        print("\n🎉 All key application pages are accessible!")
    else:
        print("\n⚠️ Some application pages are not accessible.")
    
    return all_pages_ok

def check_docker_status():
    """Check if the Docker containers are running"""
    print("Checking Docker container status...")
    
    try:
        result = subprocess.run(
            ["docker-compose", "ps"],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"❌ Error running docker-compose ps: {result.stderr}")
            return False
        
        print("\nDocker container status:")
        print(result.stdout)
        
        if "Up" not in result.stdout:
            print("❌ Web container doesn't appear to be running.")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error checking Docker status: {e}")
        return False

if __name__ == "__main__":
    success = check_docker_status() and check_app_running()
    if not success:
        sys.exit(1)
    else:
        print("✅ Application check completed successfully!")
        sys.exit(0)
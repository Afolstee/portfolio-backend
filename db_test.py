import socket
import subprocess
import requests
import dns.resolver
import psycopg2
from sqlalchemy import create_engine

def test_dns_resolution():
    hostname = "db.rayangbafjrzdqxlxxrl.supabase.co"
    project_url = "https://rayangbafjrzdqxlxxrl.supabase.co"
    
    print("=== DNS Resolution Tests ===")
    
    # Test 1: Basic socket resolution
    try:
        ip = socket.gethostbyname(hostname)
        print(f"✅ socket.gethostbyname: {hostname} → {ip}")
    except socket.gaierror as e:
        print(f"❌ socket.gethostbyname failed: {e}")
    
    # Test 2: Using DNS resolver with different servers
    dns_servers = ['8.8.8.8', '1.1.1.1', '208.67.222.222']  # Google, Cloudflare, OpenDNS
    
    for dns_server in dns_servers:
        try:
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            result = resolver.resolve(hostname, 'A')
            for ip in result:
                print(f"✅ DNS Server {dns_server}: {hostname} → {ip}")
                break
        except Exception as e:
            print(f"❌ DNS Server {dns_server} failed: {e}")
    
    # Test 3: System nslookup
    try:
        result = subprocess.run(['nslookup', hostname], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ nslookup successful")
            print(f"Output: {result.stdout.strip()}")
        else:
            print(f"❌ nslookup failed: {result.stderr}")
    except Exception as e:
        print(f"❌ nslookup command failed: {e}")
    
    # Test 4: Check if project exists via HTTPS
    try:
        response = requests.get(project_url, timeout=10)
        print(f"✅ HTTPS Project URL accessible: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS Project URL failed: {e}")
    
    # Test 5: Try alternative connection methods
    print("\n=== Alternative Connection Tests ===")
    
    # Test with connection pooler (port 6543)
    pooler_url = "postgresql://postgres:YOUR_PASSWORD@db.rayangbafjrzdqxlxxrl.supabase.co:6543/postgres?sslmode=require"
    print(f"Try connection pooler: {pooler_url}")
    
    # Test with different SSL modes
    ssl_modes = ['require', 'prefer', 'allow', 'disable']
    for ssl_mode in ssl_modes:
        test_url = f"postgresql://postgres:YOUR_PASSWORD@db.rayangbafjrzdqxlxxrl.supabase.co:5432/postgres?sslmode={ssl_mode}"
        print(f"Try SSL mode '{ssl_mode}': {test_url}")

def test_network_connectivity():
    print("\n=== Network Connectivity Tests ===")
    
    # Test basic internet connectivity
    test_hosts = [
        "google.com",
        "supabase.com",
        "github.com"
    ]
    
    for host in test_hosts:
        try:
            ip = socket.gethostbyname(host)
            print(f"✅ {host} resolves to {ip}")
        except Exception as e:
            print(f"❌ {host} resolution failed: {e}")

def get_system_dns_info():
    print("\n=== System DNS Information ===")
    
    try:
        # Get system DNS configuration (Windows)
        result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        dns_lines = [line.strip() for line in lines if 'DNS Servers' in line or 'DNS' in line]
        for line in dns_lines[:5]:  # Show first 5 DNS-related lines
            print(line)
    except Exception as e:
        print(f"Could not get DNS info: {e}")

if __name__ == "__main__":
    test_dns_resolution()
    test_network_connectivity()
    get_system_dns_info()
    
    print("\n=== Recommendations ===")
    print("1. If all DNS tests fail, try changing your DNS servers to 8.8.8.8 and 8.8.4.4")
    print("2. If HTTPS works but database doesn't, try the connection pooler (port 6543)")
    print("3. Try connecting from a different network (mobile hotspot)")
    print("4. Check if your firewall/antivirus is blocking database connections")
    print("5. Verify your Supabase project is not paused in the dashboard")
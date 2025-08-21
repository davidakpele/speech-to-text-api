import socket
import requests
import subprocess
import sys

def check_port(port):
    """Check if a port is open"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def check_ollama():
    """Check if Ollama is running"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    print("=== Diagnostic Check ===")
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check ports
    ports = [8000, 8001, 8002, 11434]
    for port in ports:
        status = "Open" if check_port(port) else "Closed"
        print(f"Port {port}: {status}")
    
    # Check Ollama
    ollama_status = "Running" if check_ollama() else "Not running"
    print(f"Ollama: {ollama_status}")
    
    print("\n=== Suggestions ===")
    if not check_port(8000):
        print("1. Port 8000 is closed. Try: uvicorn main:app --reload --host 0.0.0.0 --port 8001")
    else:
        print("1. Port 8000 is open but you can't access it. Check firewall settings.")
    
    if not check_ollama():
        print("2. Ollama is not running. Make sure you've started it.")
    
    print("3. Try accessing: http://127.0.0.1:8000/ (instead of localhost)")
    print("4. Try running: uvicorn main:app --reload --host 0.0.0.0 --port 8001")

if __name__ == "__main__":
    main()
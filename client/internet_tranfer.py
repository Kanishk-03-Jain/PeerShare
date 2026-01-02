import socket
import sys
import threading
import time
import os
import stun
from client_app import config

# Configuration
CHUNK_SIZE = 1024  # UDP packets must be small (~1KB)

def get_public_ip_port():
    """Asks a Google STUN server for our Real Public IP & Port."""
    print("🌍 Finding your Public IP (STUN)... this takes a few seconds...")
    try:
        # We bind to port 0 (let OS pick) and source_ip="0.0.0.0"
        nat_type, external_ip, external_port = stun.get_ip_info(
            source_ip="0.0.0.0",
            stun_host="stun.l.google.com", 
            stun_port=19302
        )
        return external_ip, external_port
    except Exception as e:
        print(f"❌ STUN failed: {e}")
        return None, None

def listen_for_file(sock, save_path):
    """Receiver Mode: Listens for file chunks."""
    print(f"📥 Waiting for file... (Saving to {save_path})")
    try:
        with open(save_path, 'wb') as f:
            while True:
                data, addr = sock.recvfrom(CHUNK_SIZE + 100) # Buffer size
                
                # Simple "End of File" signal check
                if data == b"EOF":
                    print("\n✅ Transfer Complete!")
                    break
                
                f.write(data)
                print(".", end="", flush=True) # visual progress
    except Exception as e:
        print(f"❌ Receive error: {e}")

def send_file(sock, target_ip, target_port, filepath):
    """Sender Mode: Blasts file chunks to the target."""
    print(f"📤 Sending {filepath} to {target_ip}:{target_port}...")
    
    if not os.path.exists(filepath):
        print("❌ File not found.")
        return

    target = (target_ip, int(target_port))
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(CHUNK_SIZE):
            sock.sendto(chunk, target)
            # UDP is fast; we must sleep slightly to not overwhelm the receiver
            time.sleep(0.002) 
            print(".", end="", flush=True)
            
    # Send EOF signal multiple times (UDP is unreliable, packets get lost)
    for _ in range(5):
        sock.sendto(b"EOF", target)
        time.sleep(0.1)
    
    print("\n✅ File Sent!")

def hole_punching_transfer():
    # 1. Setup the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Bind to a local port (0 means random available port)
    sock.bind(('0.0.0.0', 0))

    # 2. Find WHO we are (Public IP)
    my_ip, my_port = get_public_ip_port()
    if not my_ip:
        print("Could not determine public IP. Aborting.")
        return

    print(f"\n📢 YOUR PUBLIC ADDRESS: {my_ip}:{my_port}")
    print("--> Share this with your friend!\n")

    # 3. Get Friend's Info
    friend_ip = input("Enter Friend's Public IP: ").strip()
    friend_port = int(input("Enter Friend's Public Port: "))
    
    mode = input("Are you (s)ending or (r)eceiving? ").lower()
    filename = input("Enter filename (e.g. test.txt): ").strip()

    # 4. THE PUNCH (Critical Step) 🥊
    # We must send data to them to open our firewall.
    # They must send data to us to open their firewall.
    print("\n🥊 Punching hole through firewall... (Press Enter on both computers simultaneously)")
    input("Press Enter to start...")

    print("Ping...", end="")
    # Send 5 dummy packets to open the hole
    for _ in range(5):
        sock.sendto(b"PUNCH", (friend_ip, friend_port))
        time.sleep(0.1)
    print(" PUNCH SENT!")

    # 5. Start Transfer
    if mode == 's':
        # Sender
        filepath = os.path.join(config.default_folder, filename) # Uses your client_app settings
        send_file(sock, friend_ip, friend_port, filepath)
    else:
        # Receiver
        save_path = os.path.join(config.download_folder, filename)
        listen_for_file(sock, save_path)

    sock.close()

if __name__ == "__main__":
    hole_punching_transfer()
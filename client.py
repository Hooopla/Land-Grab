import socket
import keyboard 

# Server Details
SERVER_IP = '127.0.0.1' # Only to connect to server if on the same machine! If not in same machine figure out server ip using ipconfig in terminal
SERVER_PORT = 12345

def start_client():
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  client.connect((SERVER_IP, SERVER_PORT))
  print("Connected to server!") # Debugging purposes

  while True:
    key = keyboard.read_event().name
    if key in ["w", "a", "s", "d", "space"]:
      client.send(key.upper().encode('utf-8'))
      print(f"Sent: {key.upper()}") # Debugging Purposes

if __name__ == "__main__":
  start_client()
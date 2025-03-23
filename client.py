import socket
import keyboard 

# Server Details
SERVER_IP = '127.0.0.1' # Only to connect to server if on the same machine! If not in same machine figure out server ip using ipconfig in terminal
SERVER_PORT = 12345

def start_client():
  client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

  try:
    client.connect((SERVER_IP, SERVER_PORT))
    server_message = client.recv(1024).decode('utf-8')
    print(f"Server: {server_message}")

    if "full" in server_message.lower():
      server_message = client.recv(1024).decode('utf-8')
      print(f"Server: {server_message}")
      client.close()
      return
    
    while True:
    # Send Keyboard inputs
      key = keyboard.read_event().name
      if key in ["w", "a", "s", "d", "space"]:
        client.send(key.upper().encode('utf-8'))
        print(f"Sent: {key.upper()}") # Debugging Purposes

        # Receieve any addtional information from server after user clicks
        # Note: Can be used for game logic/map updating? Since server will send back information

  except ConnectionRefusedError:
      print("Unable to connect to the server. Make sure the server is running.")
  except KeyboardInterrupt:
      print("Client shutting down.")
  finally:
      client.close()

if __name__ == "__main__":
  start_client()
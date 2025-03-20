import socket

# Server Information
HOST_IP = '0.0.0.0'
PORT = 12345
MAX_CLIENTS = 3 

def start_server():
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((HOST_IP, PORT))
  server.listen(MAX_CLIENTS)
  print(f"Server is now running on {HOST_IP}:{PORT}") # Debugging Purposes

  clients = [] # Hold our clients in here

  # Client Limiter ensure we only have 3 connections! Inform the user.
  while len(clients) < MAX_CLIENTS:
    client_socket, client_address = server.accept()
    print(f"{client_address} has joined the game") # Debugging Purposes
    clients.append(client_socket)
    print(f"Server Capacity: {len(clients)}/{MAX_CLIENTS}") # Debugging Purposes

  print("The server is now full!")

  while True:
    for client_socket in clients:
      try:
          data = client_socket.recv(1024).decode('utf-8')
          # If there is nothing left to be said from client disconnect
          if not data:
            print("A player has left the game.")
            clients.remove(client_socket)
            client_socket.close()
          # Output the user's input
          else:
            print(f"Received: {data}")
      except ConnectionResetError:
        print("[ERROR] A player has disconnected.")
        clients.remove(client_socket)
        client_socket.close()

if __name__ == "__main__":
    start_server()
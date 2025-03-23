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

  while True:
    # Accepts Clients if not FULL
    if len(clients) < MAX_CLIENTS:
      client_socket, client_address = server.accept()
      print(f"{client_address} has joined the game") # Debugging Purposes
      clients.append(client_socket)
      print(f"Server Capacity: {len(clients)}/{MAX_CLIENTS}") # Debugging Purposes
      client_socket.send("Welcome to the server!".encode('utf-8'))
    # Declines Clients if FULL
    else:
      client_socket, client_address = server.accept()
      print(f"Connection from {client_address} is denied because server is full.")
      client_socket.send("Server is full. Please try again later.".encode('utf-8'))
      client_socket.close()
    
    # Handle client commands!
    for client_socket in clients:
      try:
          data = client_socket.recv(1024).decode('utf-8')
          # If there is nothing left to be said from client disconnect
          if not data:
            print(f"{client_socket.getpeername()} left the game.")
            clients.remove(client_socket)
            client_socket.close()
          # Output the user's input
          else:
            print(f"Received from {client_socket.getpeername()}: {data}")
      except ConnectionResetError:
        print(f"[ERROR] {client_socket.getpeername()} left the game.")
        clients.remove(client_socket)
        client_socket.close()

if __name__ == "__main__":
    start_server()
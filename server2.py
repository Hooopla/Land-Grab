import socket
import select

# Server Variables/Information
HOST_IP = '0.0.0.0'
PORT = 12345
MAX_CLIENTS = 2

def start_server():
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.bind((HOST_IP, PORT))
  server.listen(MAX_CLIENTS)
  print(f"Server is up on {HOST_IP}:{PORT}") # Debugging Purposes

  clients = [] # Hold a list of connected clients

  while True:
    ready_to_read, _, _ = select.select([server] + clients, [], [])

    for sock in ready_to_read:
      if sock == server:
        if len(clients) < MAX_CLIENTS:
        # If there is space on the server accept clients
          client_socket, client_address = server.accept()
          print(f"{client_address} has joined the game." )
          clients.append(client_socket)
          print(f"Server Capacity: {len(clients)} / {MAX_CLIENTS}")
          client_socket.send("Welcome to the server!".encode('utf-8'))
        else:
          client_socket, client_address = server.accept()
          print(f"Connection from {client_address} is declined because server is currently full.")
          client_socket.send("Server is full. Please try again later.".encode('utf-8'))
          client_socket.close()
      else:
        try:
          data = sock.recv(1024).decode('utf-8')
          if not data:
            # Disconnect
            print(f"{socket.getpeername()} has left the game.")
            clients.remove(sock)
            sock.close()
          else:
            print(f"Received from {sock.getpeername()}: {data}")
        except ConnectionResetError:
          print(f"[ERROR] {sock.getpeername()} left the game.")
          clients.remove(sock)
          sock.close()

if __name__ == "__main__":
    start_server()

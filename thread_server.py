import socket
import threading

# Server Variables/Information
HOST_IP = '0.0.0.0'
PORT = 12345
MAX_CLIENTS = 2

def print_server_capacity(current, capacity):
    print(f"Server Capacity: {current} / {capacity}")
    return

def handle_client(client_socket, client_address, clients):
    try:
        print(f"{client_address} has joined the game.")
        client_socket.send("Welcome to the server!".encode('utf-8'))
        print_server_capacity(len(clients), MAX_CLIENTS)

        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                # Disconnect
                print(f"{client_address} has left the game.")
                clients.remove(client_socket)
                client_socket.close()
                print_server_capacity(len(clients), MAX_CLIENTS)
                break
            else:
                print(f"Received from {client_address}: {data}")

    except ConnectionResetError:
        print(f"[ERROR] {client_address} disconnected unexpectedly.")
        clients.remove(client_socket)
        client_socket.close()
        print_server_capacity(len(clients), MAX_CLIENTS)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST_IP, PORT))
    server.listen(MAX_CLIENTS)
    print(f"Server is up on {HOST_IP}:{PORT}")  # Debugging Purposes

    clients = []  # Hold a list of connected clients

    while True:
        if len(clients) < MAX_CLIENTS:
            client_socket, client_address = server.accept()
            clients.append(client_socket)

            # Start a new thread for the client
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address, clients))
            client_thread.start()

        else:
            client_socket, client_address = server.accept()
            print(f"Connection from {client_address} is declined because server is currently full.")
            client_socket.send("Server is full. Please try again later.".encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()

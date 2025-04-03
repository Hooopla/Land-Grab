import socket
import threading
import json
import time
from Player import Player

# Server Variables/Information
HOST_IP = '0.0.0.0'
PORT = 12345
MAX_CLIENTS = 3
clients = []  # Hold a list of connected clients
available_player_ids = set(range(MAX_CLIENTS)) # set of available IDs
server_start_time = time.time()

def print_server_capacity(current, capacity):
    print(f"Server Capacity: {current} / {capacity}")
    return

def get_server_age():
    return int(time.time() - server_start_time)

def broadcast_positions():
    ''' Broadcasts all player positions to every client at a fixed interval. '''
    while True:
        if len(clients) > 0:

            # Create the list of player positions
            positions = [{"id": player.player_id, "x": player.x_pos, "y": player.y_pos} for player in clients]

            # Convert to json to send to all clients
            message = json.dumps({"TYPE": "UPDATE",
                                  "players": positions,
                                  "age": get_server_age()}) + "\n"
            for player in clients:
                try:
                    player.client_socket.sendall(message.encode())
                except:
                    print(f"[ERROR] Unable to send data to {player.client_address}")
        
        time.sleep(0.01) # Send updates every 0.01 seconds

def handle_client(player: Player):
    try:
        print(f"{player.client_address} has joined the game.")
        welcome_message = json.dumps({"TYPE": "TEXT", "message": "Welcome to the server!"}) + "\n"
        player.client_socket.send(welcome_message.encode('utf-8'))
        print_server_capacity(len(clients), MAX_CLIENTS)

        while True:
            data = player.client_socket.recv(1024).decode('utf-8')
            if not data:
                # Disconnect
                print(f"{player.client_address} has left the game.")
                clients.remove(player)
                player.client_socket.close()
                print_server_capacity(len(clients), MAX_CLIENTS)
                break
            else:
                #print(f"Received from {player.client_address}: {data}")

                data_dict = json.loads(data)
                match data_dict["TYPE"]:
                    case "MOVE":
                        player.update_position(data_dict['direction_x'], data_dict['direction_y'])
                        print(f"{player.client_address} has moved to: ({player.x_pos}, {player.y_pos})") # For debugging
                    case "SELECT":
                        if player.has_selected == False:                            
                            x = player.x_pos
                            y = player.y_pos

                            # TODO: Implement Prottoy's selection logic here
                        else:
                            print(f"[ERROR] {player.client_address} tried to SELECT but already has!")
                    case _:
                        print(f"[ERROR] Invalid packet type: {data_dict['TYPE']}")

                #client_socket.send("ACK".encode('utf-8'))

            # Regardless, run:
            player.update_position(0,0) # TODO: test this

    except ConnectionResetError:
        print(f"[ERROR] {player.client_address} disconnected unexpectedly.")

    finally:
        clients.remove(player)
        available_player_ids.add(player.player_id)  # add id back to available ids
        player.client_socket.close()
        print_server_capacity(len(clients), MAX_CLIENTS)


def start_server():
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST_IP, PORT))
    server.listen(MAX_CLIENTS)
    print(f"Server is up on {HOST_IP}:{PORT}")  # Debugging Purposes

    # Start the broadcasting thread
    broadcast_thread = threading.Thread(target=broadcast_positions, daemon=True)
    broadcast_thread.start()

    while True:
        if len(clients) < MAX_CLIENTS:
            client_socket, client_address = server.accept()
            
            player_id = min(available_player_ids)   # get the smallest available id
            available_player_ids.remove(player_id)  # mark the id as used
            
            new_player = Player(player_id, client_socket, client_address) # Store client socket/address info
            clients.append(new_player)

            # Start a new thread for the client
            client_thread = threading.Thread(target=handle_client, args=(new_player,))
            client_thread.start()

        else:
            client_socket, client_address = server.accept()
            print(f"Connection from {client_address} is declined because server is currently full.")
            client_socket.send("Server is full. Please try again later. \n".encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    start_server()
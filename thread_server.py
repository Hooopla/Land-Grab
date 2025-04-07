# thread_server.py
import socket
import threading
import json
import time
from Player import Player
from generate_game_board import generate_game_board
from board_utils import count_region_cells

# Server Variables/Information
HOST_IP = '0.0.0.0'
PORT = 12345
MAX_CLIENTS = 3
clients = []  # Hold a list of connected clients
available_player_ids = set(range(MAX_CLIENTS)) # set of available IDs
server_start_time = time.time()
data_lock = threading.Lock() # To prevent 2 threads from accessing the same data and corrupting it

# Board Info (same as on client side)
SCREEN_WIDTH = 1520
SCREEN_HEIGHT = 960
ROWS, COLS = 7, 9
CELL_WIDTH = 85
CELL_HEIGHT = 85
total_board_width = CELL_WIDTH * COLS
total_board_height = CELL_HEIGHT * ROWS
BOARD_OFFSET_X = (SCREEN_WIDTH - total_board_width) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - total_board_height) // 2
game_board = None

# USE DATA LOCK ON THESE
show_outlines = True
show_full_shapes = False
show_grid_outlines = False
region_revealed = [False, False, False]

# Track which player claimed which region
region_owner = [None, None, None]
round_start_time = None
round_in_progress = False
ROUND_DURATION = 10




def print_server_capacity(current, capacity):
    print(f"Server Capacity: {current} / {capacity}")
    return

def get_server_age():
    return int(time.time() - server_start_time)

def check_ready_status():
    ''' Checks if all connected players are ready and sends the board if they are. '''
    global game_board, round_in_progress, round_start_time

    # Count the ready players
    players_ready = 0
    for player in clients:
        if player.is_ready:
            players_ready += 1
    print(f"{players_ready} / {MAX_CLIENTS} are ready!")

    # If all players are ready, and round hasn't already started
    if players_ready == MAX_CLIENTS and not round_in_progress:
        print("All players are reading. Starting the round!")
        round_start_time = time.time()
        round_in_progress = True
        game_board = generate_game_board(ROWS, COLS)

        # Broadcast the game board to all clients
        message = json.dumps({"TYPE": "START_ROUND", "game_board": game_board}) + "\n"
        for player in clients:
            player.client_socket.sendall(message.encode())

        # Start the round timer thread
        timer_thread = threading.Thread(target=round_timer_thread, daemon=True)
        timer_thread.start()

def round_timer_thread():
    ''' Thread to constantly keep track of how much time is left in the round. '''
    global round_in_progress

    while time.time() - round_start_time < ROUND_DURATION:
        time.sleep(0.1)
        if all(p.has_selected for p in clients):
            print("All players have selected before time as run out. Ending round.")
            break
    
    # If round duration timer is up
    if round_in_progress:
        print(f"{ROUND_DURATION} seconds passed or all have selected. Ending round.")
        end_round()


def end_round():
    ''' Handles any cleanup or resetting needed between rounds. '''
    global region_revealed, region_owner, round_in_progress, game_board

    round_in_progress = False

    # determine a winner
    if not all(region_revealed):
        broadcast_winner(None)
    else:
        check_winner()

    # create a brief pause as to not reset instantly
    time.sleep(4)

    # reset the data
    with data_lock:
        region_revealed = [False, False, False]
        region_owner = [None, None, None]
        game_board = None

        for player in clients:
            player.has_selected = False
            player.is_ready = False
            
            # reset position
            player.y_pos = SCREEN_HEIGHT - 100
            player.x_pos = int((SCREEN_WIDTH // 6) * (1 + 2 * player.player_id))

    message = json.dumps({"TYPE": "RESET_ROUND"}) + "\n"
    for player in clients:
        player.client_socket.sendall(message.encode())

def broadcast_winner(winner_player_id):
    '''
    Sends an 'END_ROUND' packet to all clients announcing the winner of the round.
    '''
    message_dict = {
        "TYPE": "END_ROUND",
        "winner": winner_player_id
    }
    message = json.dumps(message_dict) + "\n"
    for player in clients:
        try:
            player.client_socket.sendall(message.encode())
        except Exception as e:
            print(f"ERROR: Unable to send winner data to player {player.player_id}: {e}")

def check_winner():
    ''' 
    Checks if all regions have been revealed. If so, counts cells in each region and then determines which
    region has the most cells. The player who claimed that region is declared and announced the winner.
    '''
    global game_board, region_revealed
    
    # Check if there is a winner
    if all(region_revealed):
        # Count cells in each region
        region_cell_counts = count_region_cells(game_board)
        max_cells = max(region_cell_counts)
        winning_region = region_cell_counts.index(max_cells)
        
        # Look up the owner of the winning region
        winner_id = region_owner[winning_region]
        
        # Announce the winner
        print(f"Player {winner_id} has won the round with {max_cells} cells!")  
        broadcast_winner(winner_id)
        

def broadcast_positions():
    ''' Broadcasts all player positions to every client at a fixed interval. '''
    while True:
        if len(clients) > 0:

            # Create the list of player positions
            positions = [{"id": player.player_id, "x": player.x_pos, "y": player.y_pos} for player in clients]

            message = None
            with data_lock:
                # Convert to json to send to all clients
                message = json.dumps({"TYPE": "UPDATE",
                                    "players": positions,
                                    "show_outlines": show_outlines,
                                    "show_full_shapes": show_full_shapes,
                                    "show_grid_outlines": show_grid_outlines,
                                    "region_revealed": region_revealed,
                                    "region_owner": region_owner,
                                    "remaining_time": max(0, ROUND_DURATION - int(time.time() - round_start_time)) if round_in_progress else None}) + "\n"
                
            for player in clients:
                try:
                    player.client_socket.sendall(message.encode())
                except:
                    print(f"[ERROR] Unable to send data to {player.client_address}")
        
        time.sleep(0.01) # Send updates every 0.01 seconds

def handle_client(player: Player):
    global show_full_shapes, show_grid_outlines, show_outlines, region_revealed
    buffer = " "
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
            buffer += data
            while "\n" in buffer:
                #print(f"Received from {player.client_address}: {data}")
                line, buffer = buffer.split("\n", 1)
                data_dict = json.loads(line)

                match data_dict["TYPE"]:
                    case "MOVE":
                        player.update_position(data_dict['direction_x'], data_dict['direction_y'])
                        print(f"{player.client_address} has moved to: ({player.x_pos}, {player.y_pos})") # For debugging
                    
                    case "SELECT":
                        if player.has_selected == False and game_board:                            
                            x = player.x_pos
                            y = player.y_pos
                            print(f"{player.client_address} has selected: ({x}, {y})")

                            # Prottoy's selection logic
                            col_selected = int((x - BOARD_OFFSET_X) // CELL_WIDTH)
                            row_selected = int((y - BOARD_OFFSET_Y) // CELL_HEIGHT)
                            if 0 <= row_selected < ROWS and 0 <= col_selected < COLS:
                                selected_region_id = game_board[row_selected][col_selected]

                                with data_lock:
                                    if not region_revealed[selected_region_id]:
                                        region_revealed[selected_region_id] = True
                                        region_owner[selected_region_id] = player.player_id
                                        player.has_selected = True
                                        print(f"Region {selected_region_id} has been claimed by player {player.player_id}")
                                        check_winner()

                            else:
                                print(f"[WARN] Player {player.player_id} attempted invalid selection at ({row_selected}, {col_selected})")                            

                    case "READY":
                        if player.is_ready == False:
                            player.is_ready = True
                            check_ready_status()
                    
                    case _:
                        print(f"[ERROR] Invalid packet type: {data_dict['TYPE']}")


            # Regardless, run:
            player.update_position(0,0) # TODO: test this

    except ConnectionResetError:
        print(f"[ERROR] {player.client_address} disconnected unexpectedly.")

    finally:
        clients.remove(player)
        available_player_ids.add(player.player_id)  # add id back to available ids
        player.client_socket.close()
        print_server_capacity(len(clients), MAX_CLIENTS)

def physics_loop():
    """ Continuously updates player positions even when no input is received. """
    while True:
        for player in clients:
            player.update_position(0,0)
        time.sleep(1/60)

def start_server():
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST_IP, PORT))
    server.listen(MAX_CLIENTS)
    print(f"Server is up on {HOST_IP}:{PORT}")  # Debugging Purposes

    # Start the broadcasting thread
    broadcast_thread = threading.Thread(target=broadcast_positions, daemon=True)
    broadcast_thread.start()

    # Thread to continously run physics. # TODO doesn't really work currently
    physics_thread = threading.Thread(target=physics_loop, daemon=True)
    physics_thread.start()

    while True:
        if len(clients) < MAX_CLIENTS:
            client_socket, client_address = server.accept()
            
            player_id = min(available_player_ids)   # get the smallest available id
            available_player_ids.remove(player_id)  # mark the id as used
            
            new_player = Player(player_id, client_socket, client_address) # Store client socket/address info
            clients.append(new_player)

            # Move new player into the correct spawn location
            new_player.y_pos = SCREEN_HEIGHT - 100
            new_player.x_pos = int((SCREEN_WIDTH // 6) * (1 + 2 * new_player.player_id))

            # Start a new thread for the client
            client_thread = threading.Thread(target=handle_client, args=(new_player,))
            client_thread.start()

        else:
            client_socket, client_address = server.accept()
            server_full_message = json.dumps({"TYPE": "FULL_SERVER", "message": "Server is full please try again later."}) + "\n"
            client_socket.send(server_full_message.encode('utf-8'))
            print(f"Connection from {client_address} is declined because server is currently full.")
            client_socket.close()

if __name__ == "__main__":
    start_server()
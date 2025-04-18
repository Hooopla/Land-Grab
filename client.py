# thread_client.py
import socket
import threading
import pygame
import json
import time
import sys
from board_utils import draw_grid_outlines, draw_shape_outlines, reveal_shapes

# Server Details
SERVER_IP = '127.0.0.1'  # Only to connect to server if on the same machine!
SERVER_PORT = 12345
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create client as a global variable
buffer = "" # Store all incoming data into a buffer

# Pygame Details
pygame.init()
SCREEN_WIDTH = 1520
SCREEN_HEIGHT = 960
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Client")
running = True
text_font = pygame.font.SysFont("Arial", 30) # Default font to pass into draw_text
PLAYER_COLOURS = ["red", "blue", "green", "purple", "orange"]

# Store player data globally
player_data = {"players": []}
data_lock = threading.Lock()    # To prevent 2 threads from accessing the same data and corrupting it
remaining_time = 0
server_full = False
server_offline = False
display_controls = False
display_ready = False

# Board Details
ROWS, COLS = 7, 9
CELL_WIDTH = 85
CELL_HEIGHT = 85
total_board_width = CELL_WIDTH * COLS
total_board_height = CELL_HEIGHT * ROWS
BOARD_OFFSET_X = (SCREEN_WIDTH - total_board_width) // 2
BOARD_OFFSET_Y = (SCREEN_HEIGHT - total_board_height) // 2
game_board = None

show_outlines = True
show_full_shapes = False
show_grid_outlines = False
region_revealed = [False, False, False]

# Track region ownership
region_owner = [None, None, None]

# Message for winner
winner_message = ""

def send_data():
    ''' Countinously handles inputs and sends data to the server when needed. '''
    while True:
        # Send Keyboard inputs
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0,0)
        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        # Send a "select" packet to the server
        if keys[pygame.K_SPACE] and game_board:
            try:
                data_dict = {"TYPE": "SELECT"}
                data = json.dumps(data_dict) + "\n"
                client.send(data.encode())
            except Exception as e:
                print(f"Error sending SELECT: {e}")

        # Send a "ready" packet to the server
        if keys[pygame.K_p]:
            try:
                data_dict = {"TYPE": "READY"}
                data = json.dumps(data_dict) + "\n"
                client.send(data.encode())
            except Exception as e:
                print(f"Error sending data during ready: {e}")
                break
        

        # If input is being received, notify the server
        if direction.length() > 0:
            direction = direction.normalize()

            # Use a JSON object to send the data
            data_dict = {
                "TYPE": "MOVE",
                "direction_x": direction.x,
                "direction_y": direction.y,
            }
            data = json.dumps(data_dict) + "\n"
            try:
                client.send(data.encode())
            except Exception as e:
                print(f"Error sending data: {e}")
                break
        
        time.sleep(0.01) # Limit the amount of packets sent per second


def receive_data():
    ''' Continuously receives and processes data from the server. '''
    
    global buffer, player_data, remaining_time, game_board, show_outlines
    global show_full_shapes, show_grid_outlines, region_revealed, region_owner, winner_message
    
    
    while True:
        try:
            # Stores received data in a buffer, ensures that if 2 messages come "combined," they are parsed correctly
            buffer += client.recv(1024).decode('utf-8')
            
            # Process all complete messages (messages that end in a newline)
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1) # extract 1 full message
                dict_data = json.loads(message)

                # Handle message based on its TYPE field
                match dict_data["TYPE"]:
                    
                    case "TEXT":
                        # Simple text from the server (for printing to client console)
                        print(f"Server: {dict_data['message']}")
                    
                    case "UPDATE":
                        # Game state update from the server
                        with data_lock: # Prevents race conditions
                            player_data = dict_data # Store the latest info globally (for draw_players)
                        remaining_time = dict_data["remaining_time"]
                        show_outlines = dict_data["show_outlines"]
                        show_full_shapes = dict_data["show_full_shapes"]
                        show_grid_outlines = dict_data["show_grid_outlines"]
                        region_revealed = dict_data["region_revealed"]
                        region_owner = dict_data.get("region_owner", [None, None, None])

                    
                    case "START_ROUND":
                        # New game board received from the server
                        game_board = dict_data["game_board"]
                        print(f"Received game board from server: {game_board}")
                        
                    case "FULL_SERVER":
                        # Server is full, cannot join
                        print(f"Server is currently full please try again later.")
                        global server_full
                        server_full = True
                    
                    case "END_ROUND":
                        # Round has ended, winner announced
                        winner = dict_data["winner"]
                        if winner != None:
                            winner = winner + 1
                            print(f"Round has ended. Winner: Player {winner}") # debug statements
                            winner_message = f"Game Over! Player {winner} is the winner!"
                        else:
                            print("Not everyone selected, so no winner has been declared!") # debug statement
                            winner_message = "Not everyone selected! No winner decided."

                    case "RESET_ROUND":
                        # Reset board/winner message in preperation for the new round
                        print("Round is being reset...")
                        game_board = None
                        winner_message = None

                    case _:
                        # Unknown message type received
                        print(f"Invalid type: {dict_data['TYPE']}")
                
        except Exception as e:
            print(f"Error receiving data from server: {e}")
            break

def start_client():
    ''' Starts the client and any threads needed. '''
    try:
        client.connect((SERVER_IP, SERVER_PORT))

        # Start separate threads for sending and receiving data
        send_thread = threading.Thread(target=send_data, daemon=True)
        receive_thread = threading.Thread(target=receive_data, daemon=True)

        send_thread.start()
        receive_thread.start()

        # Wait for threads to finish (you can also use `join()` here if needed)
        #send_thread.join()
        #receive_thread.join()

    except ConnectionRefusedError:
        print("Unable to connect to the server. Make sure the server is running.")
        global server_offline 
        server_offline = True
    except KeyboardInterrupt:
        print("Client shutting down.")


# Unused, but just for demonstration of how the packets look
test_packet = {
    "TYPE": "UPDATE",
    "players": [
        {"id": 1, "x": 100, "y": 200, "name": "Player1"},
        {"id": 2, "x": 300, "y": 400, "name": "Player2"}
    ]
}

def draw_players():
    ''' Draws all the players on the screen, based on the list of player coordinates. '''

    with data_lock:  # To prevent 2 threads from accessing the same info at the same time
        for player in player_data["players"]:
            color = PLAYER_COLOURS[player["id"] % len(PLAYER_COLOURS)]
            pos = (player["x"], player["y"])
            radius = 25
            outline_width = 5  # Adjust thickness of border as needed

            # Draw gray outline
            pygame.draw.circle(screen, (128, 128, 128), pos, radius + outline_width)
            # Draw player circle
            pygame.draw.circle(screen, color, pos, radius)


def draw_board():
    ''' Draws the game board and any outlines if enabled. '''
    global game_board

    if game_board:
        reveal_shapes(screen, game_board, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT,
                      BOARD_OFFSET_X, BOARD_OFFSET_Y, PLAYER_COLOURS, region_revealed, region_owner)
        if show_outlines:
            draw_shape_outlines(screen, game_board, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT,
                                BOARD_OFFSET_X, BOARD_OFFSET_Y, "white")
        if show_grid_outlines:
            draw_grid_outlines(screen, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT,
                               BOARD_OFFSET_X, BOARD_OFFSET_Y, "white")



def draw_text(text, font, colour, x, y):
    ''' Helper function to draw any text to the screen. '''
    if text == "None":
        text = ""
    img = font.render(text, True, colour)
    screen.blit(img, (x, y))

def display_controls_ui():
    ''' Logic to draw the controls text to the screen. '''
    global display_controls
    if display_controls:
        lines = [
            "IN-GAME Controls",
            "'SPACE' - Claim tiles",
            "",
            "LOBBY Controls",
            "'P' - Ready/Unready"
        ]
    else:
        lines = [
            "Press 'ESC' for controls",
            "",
            "",
            "",
            ""
        ]

    # Set the initial position at the top-right corner
    margin_right = 10
    margin_top = 10
    x = screen.get_width() - margin_right
    y = margin_top

    # Draw the text to the screen
    for line in lines:
        text_surface = text_font.render(line, True, (255, 255, 255))
        text_width = text_surface.get_width()
        draw_text(line, text_font, (255, 255, 255), x - text_width, y)
        y += text_surface.get_height() + 5

def display_ready_ui():
    ''' Logic to draw the ready/not ready text to the screen. '''
    global display_ready

    # Colors for ready and not ready
    ready_color = (0, 255, 0) # Green
    not_ready_color = (255, 0, 0) # Red

    if display_ready:
        lines = [
            "READY",
        ]
        text_color = ready_color
    else:
        lines = [
            "NOT READY",
        ]
        text_color = not_ready_color

    # Set margins
    margin_left = 10
    margin_bottom = 10

    # Calculate total height of the block
    total_height = sum(text_font.render(line, True, (255, 255, 255)).get_height() + 5 for line in lines) - 5

    # Position at bottom-left
    x = margin_left
    y = screen.get_height() - margin_bottom - total_height

    # Draw the actual text to the screen
    for line in lines:
        text_surface = text_font.render(line, True, text_color)
        draw_text(line, text_font, text_color, x, y)
        y += text_surface.get_height() + 5


if __name__ == "__main__":
    start_client()

    # Pygame display loop
    while running:

        screen.fill("black") # clear the screen

        # If the server is full, display the full message and exit
        if server_full:
            full_server_msg = "Server is currently full, please try again later."
            close_msg = "This tab will close momentarily"
            # Get rendered surfaces
            msg1_surface = text_font.render(full_server_msg, True, (255, 255, 255))

            # Get X and Y for first message
            x = screen.get_width() // 3
            y = screen.get_height() // 2

            # Draw both messages, stacked
            draw_text(full_server_msg, text_font, (255, 255, 255), x, y)
            draw_text(close_msg, text_font, (255, 255, 255), x, y + msg1_surface.get_height() + 10)  # 10 pixels spacing
            pygame.display.update()  # Ensure the message is shown
            time.sleep(3)
            break

        # If server is not online 
        if server_offline: 
            no_available_server_msg = "No available server, please try again later."
            close_msg = "This tab will close momentarily"
            # Get rendered surfaces
            msg1_surface = text_font.render(no_available_server_msg, True, (255, 255, 255))

            # Get X and Y for first message
            x = screen.get_width() // 3
            y = screen.get_height() // 2

            # Draw both messages, stacked
            draw_text(no_available_server_msg, text_font, (255, 255, 255), x, y)
            draw_text(close_msg, text_font, (255, 255, 255), x, y + msg1_surface.get_height() + 10)  # 10 pixels spacing
            pygame.display.update()  # Ensure the message is shown
            time.sleep(3)
            break

        # Poll for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    display_controls = not display_controls
                elif event.key == pygame.K_p:
                    display_ready = True
        
        # Call all draw functions
        display_ready_ui()
        display_controls_ui()
        draw_board()
        draw_players()
        draw_text(str(remaining_time), text_font, (255,255,255), 0, 0)
        
        # Display the winner message underneath the board
        if winner_message:
            draw_grid_outlines(screen, ROWS, COLS, CELL_WIDTH, CELL_HEIGHT, BOARD_OFFSET_X, BOARD_OFFSET_Y, "white")

            # Default to white color
            winner_color = (255, 255, 255)

            # Try to extract winner index from the message
            if "Player" in winner_message:
                try:
                    winner_num = int(winner_message.split("Player")[1].split()[0]) - 1  # subtract one due to indexing.
                    winner_color = pygame.Color(PLAYER_COLOURS[winner_num % len(PLAYER_COLOURS)])
                except Exception as e:
                    print(f"Failed to extract winner color: {e}") # For debug purposes

            draw_text(winner_message, text_font, winner_color, screen.get_width() // 3, screen.get_height() - 150)
            display_ready = False
        pygame.display.update()

    client.close()
    pygame.quit()
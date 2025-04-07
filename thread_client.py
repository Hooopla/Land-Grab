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
display_controls = False

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

        if keys[pygame.K_SPACE] and game_board:
            try:
                data_dict = {"TYPE": "SELECT"}
                data = json.dumps(data_dict) + "\n"
                client.send(data.encode())
            except Exception as e:
                print(f"Error sending SELECT: {e}")


        if keys[pygame.K_p]:       # "READY"
            try:
                data_dict = {"TYPE": "READY"}
                data = json.dumps(data_dict) + "\n"
                client.send(data.encode())
            except Exception as e:
                print(f"Error sending data during ready: {e}")
                break
        # If input is being recieved
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
    
    global buffer, player_data, remaining_time, game_board, show_outlines, show_full_shapes, show_grid_outlines, region_revealed, region_owner, winner_message
    while True:
        try:
            # Stores recieved data in a buffer, ensures that if 2 messages come "combined," they are parsed correctly
            buffer += client.recv(1024).decode('utf-8')
            while "\n" in buffer:
                message, buffer = buffer.split("\n", 1) # extract 1 full message
                dict_data = json.loads(message)

                # Based on the "TYPE", handle the data accordingly
                match dict_data["TYPE"]:
                    
                    case "TEXT":
                        print(f"Server: {dict_data['message']}")
                    
                    case "UPDATE":
                        with data_lock: # Prevents race conditions
                            player_data = dict_data # Store the latest info globally (for draw_players)
                        remaining_time = dict_data["remaining_time"]
                        show_outlines = dict_data["show_outlines"]
                        show_full_shapes = dict_data["show_full_shapes"]
                        show_grid_outlines = dict_data["show_grid_outlines"]
                        region_revealed = dict_data["region_revealed"]
                        region_owner = dict_data.get("region_owner", [None, None, None])

                    
                    case "START_ROUND":
                        game_board = dict_data["game_board"]
                        print(f"Recieved game board from server: {game_board}")
                        
                    case "FULL_SERVER":
                        print(f"Server is currently full please try again later.")
                        global server_full
                        server_full = True
                    
                    case "END_ROUND":
                        winner = dict_data["winner"]
                        print(f"Round has ended. Winner: Player {winner}") # debug statements
                        winner_message = f"Game Over! Player {winner} is the winner!"

                    case "RESET_ROUND":
                        print("Round is being reset...")
                        game_board = None
                        winner_message = None

                    case _:
                        print(f"Invalid type: {dict_data['TYPE']}")
                
        except Exception as e:
            print(f"Error receiving data from server: {e}")
            break

def start_client():

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

    with data_lock: # To prevent 2 threads from accessing the same info at the same time
        for player in player_data["players"]:
            pygame.draw.circle(screen, PLAYER_COLOURS[player["id"] % len(PLAYER_COLOURS)], (player["x"], player["y"]), 25)


def draw_board():
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
    img = font.render(text, True, colour)
    screen.blit(img, (x, y))

def display_controls_ui():
    global display_controls
    if display_controls:
        lines = [
            "IN-GAME Controls",
            "'SPACE' - Claim tiles",
            "",
            "LOBBY Controls",
            "'Q' - Ready/Unready"
        ]

        # Set the initial position at the top-right corner
        margin_right = 10
        margin_top = 10
        x = screen.get_width() - margin_right
        y = margin_top

        for line in lines:
            text_surface = text_font.render(line, True, (255, 255, 255))
            text_width = text_surface.get_width()
            draw_text(line, text_font, (255, 255, 255), x - text_width, y)
            y += text_surface.get_height() + 5
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

        for line in lines:
            text_surface = text_font.render(line, True, (255, 255, 255))
            text_width = text_surface.get_width()
            draw_text(line, text_font, (255, 255, 255), x - text_width, y)
            y += text_surface.get_height() + 5

if __name__ == "__main__":
    start_client()

    # Pygame display loop (make its own function?)
    while running:

        screen.fill("black") # clear the screen

        # If the server is full, display the full message and exit
        if server_full:
            draw_text("Server is full, please try again later.", text_font, (255, 255, 255), screen.get_width() // 3, screen.get_height() // 2)
            pygame.display.update()  # Ensure the message is shown
            time.sleep(5)
            break

        # Poll for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    display_controls = not display_controls
                

        display_controls_ui()
        draw_board()
        draw_players()
        draw_text(str(remaining_time), text_font, (255,255,255), 0, 0)
        
        # Display the winner message underneath the board
        if winner_message:
            draw_text(winner_message, text_font, (255,255,255), screen.get_width() // 3, screen.get_height() - 150)

        pygame.display.update()

    client.close()
    pygame.quit()
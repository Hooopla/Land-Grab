# WIP 
import socket
import threading
import pygame
import json
import time

# Server Details
SERVER_IP = '127.0.0.1'  # Only to connect to server if on the same machine!
SERVER_PORT = 12345
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create client as a global variable
buffer = "" # Store all incoming data into a buffer

# Pygame Details
pygame.init()
screen = pygame.display.set_mode((1280, 720))
pygame.display.set_caption("Client")
running = True

# Store player data globally
player_data = {"players": []}
data_lock = threading.Lock()    # To prevent 2 threads from accessing the same data and corrupting it

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

        # If input is being recieved
        if direction.length() > 0:
            direction = direction.normalize()

            # Use a JSON object to send the data
            data_dict = {
                "TYPE": "MOVE",
                "direction_x": direction.x,
                "direction_y": direction.y,
            }
            data = json.dumps(data_dict)
            try:
                client.send(data.encode())
            except Exception as e:
                print(f"Error sending data: {e}")
                break
        
        time.sleep(0.01) # Limit the amount of packets sent per second


def receive_data():
    
    global buffer, player_data

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
                    
                    case _:
                        print(f"Invalid type: {dict_data['TYPE']}")
                
        except Exception as e:
            print(f"Error receiving data from server: {e}")
            break

def start_client():

    try:
        client.connect((SERVER_IP, SERVER_PORT))

        '''
        # Wait for the initial server message after connection
        server_message = client.recv(1024).decode('utf-8')
        print(f"Server: {server_message}")

        if "full" in server_message.lower():
            server_message = client.recv(1024).decode('utf-8')
            print(f"Server: {server_message}")
            client.close()
            return
        '''
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
    finally:
        #client.close()
        pass


test_packet = {
    "TYPE": "UPDATE",
    "players": [
        {"id": 1, "x": 100, "y": 200, "name": "Player1"},
        {"id": 2, "x": 300, "y": 400, "name": "Player2"}
    ]
}

def draw_players():
    ''' Draws all the players on the screen, based on the list of player coordinates. '''

    colours = ["red", "blue", "green", "purple", "orange"]

    with data_lock: # To prevent 2 threads from accessing the same info at the same time
        for player in player_data["players"]:
            pygame.draw.circle(screen, colours[player["id"] % len(colours)], (player["x"], player["y"]), 25)


if __name__ == "__main__":
    start_client()

    # Pygame display loop (make its own function?)
    while running:

        screen.fill("black") # clear the screen

        # Poll for events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        draw_players()

        pygame.display.update()

    client.close()
    pygame.quit()
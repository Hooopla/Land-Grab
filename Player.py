import pygame

class Player():
    def __init__(self, player_id, client_socket, client_address):
        
        # Networking Info
        self.client_socket = client_socket
        self.client_address = client_address
         
        self.player_id = player_id  # Unique number given by the server
        self.has_selected = False   # Has the player "locked in" their answer for the round?
        self.score = 0              # Player's score throughout all rounds
        self.is_ready = False       # Is the player ready to start the game?

        # Movement Info
        self.x_pos = 0
        self.y_pos = 0
        
        self.velocity = pygame.Vector2(0,0)
        self.acceleration = 750     # How fast you speed up
        self.friction = 0.855       # Slows you down smoothly (lower number --> more friction)
        self.max_speed = 500        # Maximum Speed

    # TODO: Possibly add some sort of deltatime
    def update_position(self, x_dir, y_dir):
        ''' Given an x and y input from the player, calculate the new position. '''
        
        self.direction = pygame.Vector2(x_dir, y_dir)

        # If input is being recieved
        if self.direction.length() > 0:

            # Apply acceleration
            self.velocity += self.direction * self.acceleration

            # Cap Speed
            if self.velocity.length() > self.max_speed:
                self.velocity = self.velocity.normalize() * self.max_speed

        # If no input, apply friction
        else:
            self.velocity *= self.friction

        # Update Position
        self.x_pos += self.velocity.x
        self.y_pos += self.velocity.y
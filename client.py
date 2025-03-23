import socket
import keyboard
import threading

# Server Details
SERVER_IP = '127.0.0.1' # Only to connect to server if on the same machine! If not in same machine figure out server ip using ipconfig in terminal
SERVER_PORT = 12345
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def recieve_messages():

  while True:
    try:
      data = client.recv(1024).decode()
      if not data:
        print("(ERROR) Server closed the connection.")
        break
    
      print(f"Server: {data}")
    
    except Exception as e:
      print(f"(ERROR) Connection lost: {e}")
      break


def start_client():
  


  try:
    client.connect((SERVER_IP, SERVER_PORT))
    
    recv_thread = threading.Thread(target=recieve_messages, daemon=True)
    recv_thread.start()

    '''
    server_message = client.recv(1024).decode('utf-8')
    print(f"Server: {server_message}")

    if "full" in server_message.lower():
      server_message = client.recv(1024).decode('utf-8')
      print(f"Server: {server_message}")
      client.close()
      return
    '''
    
    while True:
    # Send Keyboard inputs
      key = keyboard.read_event().name
      if key in ["w", "a", "s", "d", "space"]:
        client.send(key.upper().encode('utf-8'))
        print(f"Sent: {key.upper()}") # Debugging Purposes

        '''
        # Receieve any addtional information from server after user clicks
        # Note: Can be used for game logic/map updating? Since server will send back information
        try:
           response = client.recv(1024).decode('utf-8')
           if response:
              print(f"Server: {response}")
        except:
           pass # Ignore errors if there was no msgs
        '''

  except ConnectionRefusedError:
      print("Unable to connect to the server. Make sure the server is running.")
  except KeyboardInterrupt:
      print("Client shutting down.")
  finally:
      client.close()

if __name__ == "__main__":
  start_client()
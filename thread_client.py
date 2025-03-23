# WIP 
import socket
import keyboard
import threading

# Server Details
SERVER_IP = '127.0.0.1'  # Only to connect to server if on the same machine!
SERVER_PORT = 12345

def send_data(client):
    while True:
        # Send Keyboard inputs
        key = keyboard.read_event(suppress=True).name
        if key in ["w", "a", "s", "d", "space"]:
            client.send(key.upper().encode('utf-8'))
            print(f"Sent: {key.upper()}")  # Debugging Purposes

def receive_data(client):
    while True:
        try:
            # Receive any additional information from the server after user clicks
            server_response = client.recv(1024).decode('utf-8')
            if server_response:
                print(f"Server: {server_response}")
        except Exception as e:
            print(f"Error receiving data from server: {e}")
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((SERVER_IP, SERVER_PORT))

        # Wait for the initial server message after connection
        server_message = client.recv(1024).decode('utf-8')
        print(f"Server: {server_message}")

        if "full" in server_message.lower():
            server_message = client.recv(1024).decode('utf-8')
            print(f"Server: {server_message}")
            client.close()
            return

        # Start separate threads for sending and receiving data
        send_thread = threading.Thread(target=send_data, args=(client,))
        receive_thread = threading.Thread(target=receive_data, args=(client,))

        send_thread.start()
        receive_thread.start()

        # Wait for threads to finish (you can also use `join()` here if needed)
        send_thread.join()
        receive_thread.join()

    except ConnectionRefusedError:
        print("Unable to connect to the server. Make sure the server is running.")
    except KeyboardInterrupt:
        print("Client shutting down.")
    finally:
        client.close()

if __name__ == "__main__":
    start_client()

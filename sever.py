import socket
import threading
import os

# Base directory for file storage on the server
base_directory = "server_files"

# Ensure the base directory exists
os.makedirs(base_directory, exist_ok=True)

# Function to list files in the server's directory
def list_files():
    try:
        files = os.listdir(base_directory)
        return ";".join(files)
    except Exception as e:
        return f"Error listing files: {e}"

# Function to get the size of a file on the server
def get_file_size(filename):
    try:
        return os.path.getsize(os.path.join(base_directory, filename))
    except FileNotFoundError:
        return -1  # Indicate file not found
    except Exception as e:
        return f"Error getting file size: {e}"

# Function to handle a client connection
def handle_client(client_socket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True

    while connected:
        try:
            # Receive the request from the client
            request = client_socket.recv(1024).decode()

            if request:
                # Parse the request
                parts = request.split()
                command = parts[0]

                if command == "list_files":
                    response = list_files()
                    client_socket.send(response.encode())

                elif command == "filesize":
                    filename = parts[1]
                    file_size = get_file_size(filename)
                    if file_size == -1:
                        client_socket.send("File not found".encode())
                    else:
                        client_socket.send(str(file_size).encode())

                elif command == "download":
                    filename = parts[1]
                    start = int(parts[2])
                    end = int(parts[3])
                    safe_path = os.path.join(base_directory, filename)
                    if not os.path.abspath(safe_path).startswith(base_directory):
                        client_socket.send("Invalid file path".encode())
                        continue
                    if not os.path.exists(safe_path):
                        client_socket.send("File not found".encode())
                        continue
                    try:
                        with open(safe_path, 'rb') as f:
                            f.seek(start)
                            data = f.read(end - start)
                            client_socket.sendall(data)
                    except Exception as e:
                        client_socket.send(f"Error during download: {e}".encode())

                elif command == "upload":
                    filename = parts[1]
                    start = int(parts[2])
                    end = int(parts[3])
                    part_filename = os.path.join(base_directory, f"{filename}.part{start}")
                    try:
                        with open(part_filename, 'wb') as f:
                            bytes_received = 0
                            while bytes_received < (end - start):
                                data = client_socket.recv(min(4096, (end - start) - bytes_received))
                                if not data:
                                    break
                                f.write(data)
                                bytes_received += len(data)
                    except Exception as e:
                        client_socket.send(f"Error during upload: {e}".encode())

                elif command == "merge":
                    filename = parts[1]
                    file_size = int(parts[2])
                    num_parts = int(parts[3])
                    try:
                        with open(os.path.join(base_directory, filename), 'wb') as f:
                            for i in range(num_parts):
                                part_filename = os.path.join(base_directory, f"{filename}.part{i * (file_size // num_parts)}")
                                if os.path.exists(part_filename):
                                    with open(part_filename, 'rb') as part_file:
                                        f.write(part_file.read())
                                    os.remove(part_filename)
                    except Exception as e:
                        client_socket.send(f"Error during merge: {e}".encode())

            else:
                connected = False

        except Exception as e:
            client_socket.send(f"Error: {e}".encode())
            connected = False

    client_socket.close()
    print(f"[DISCONNECTED] {addr} disconnected.")

# Main function to start the server
def start_server(server_ip, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((server_ip, port))
    server.listen()

    print(f"[LISTENING] Server is listening on {server_ip}:{port}")

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

if __name__ == "__main__":
    SERVER_IP = "0.0.0.0"  # Listen on all available interfaces
    PORT = 12345
    start_server(SERVER_IP, PORT)

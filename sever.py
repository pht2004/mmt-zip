import socket
import threading
import os

def handle_client(client_socket):
    request = client_socket.recv(1024).decode()
    parts = request.split()
    command = parts[0]

    if command == "filesize":
        filename = parts[1]
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            client_socket.sendall(str(file_size).encode())
        else:
            client_socket.sendall(b"0")
    elif command == "download":
        filename, start, end = parts[1], int(parts[2]), int(parts[3])
        with open(filename, 'rb') as f:
            f.seek(start)
            data = f.read(end - start)
            client_socket.sendall(data)
    elif command == "upload":
        filename, start, end = parts[1], int(parts[2]), int(parts[3])
        with open(filename, 'r+b') as f:
            f.seek(start)
            data = client_socket.recv(end - start)
            f.write(data)
    client_socket.close()

def start_server(port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"Server listening on port {port}")

    while True:
        client_socket, addr = server.accept()
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()

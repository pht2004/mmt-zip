import socket
import threading
import os

SERVER_DIRECTORY = "server_files"

# Hàm xử lý từng phần download
def handle_download(client_socket, filename, start, end):
    with open(os.path.join(SERVER_DIRECTORY, filename), 'r+b') as f:
        f.seek(start)
        data = f.read(end - start)
        client_socket.sendall(data)

# Hàm xử lý từng phần upload
def handle_upload(client_socket, filename, start, end):
    with open(os.path.join(SERVER_DIRECTORY, filename), 'r+b') as f:
        f.seek(start)
        data = client_socket.recv(end - start)
        f.write(data)

# Hàm chính xử lý client
def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        parts = request.split()
        command = parts[0]

        if command == "filesize":
            filename = os.path.join(SERVER_DIRECTORY, parts[1])
            if os.path.exists(filename):
                file_size = os.path.getsize(filename)
                client_socket.sendall(str(file_size).encode())
            else:
                client_socket.sendall(b"0")

        elif command == "download":
            filename, start, end = parts[1], int(parts[2]), int(parts[3])
            download_thread = threading.Thread(target=handle_download, args=(client_socket, filename, start, end))
            download_thread.start()
            download_thread.join()  # Chờ cho đến khi download hoàn tất trước khi tiếp tục

        elif command == "upload":
            filename, start, end = parts[1], int(parts[2]), int(parts[3])
            upload_thread = threading.Thread(target=handle_upload, args=(client_socket, filename, start, end))
            upload_thread.start()
            upload_thread.join()  # Chờ cho đến khi upload hoàn tất trước khi tiếp tục

        elif command == "merge":
            filename, file_size, num_threads = parts[1], int(parts[2]), int(parts[3])
            with open(os.path.join(SERVER_DIRECTORY, filename), 'wb') as f:
                for i in range(num_threads):
                    part_filename = os.path.join(SERVER_DIRECTORY, f"{filename}.part{i * (file_size // num_threads)}")
                    with open(part_filename, 'rb') as part_file:
                        f.write(part_file.read())
                    os.remove(part_filename)

    finally:
        client_socket.close()

def start_server(port=12345):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(5)
    print(f"[*] Listening on 0.0.0.0:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    if not os.path.exists(SERVER_DIRECTORY):
        os.makedirs(SERVER_DIRECTORY)
    start_server()

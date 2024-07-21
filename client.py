import socket
import threading
import os

def get_file_size(server_ip, port, filename):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"filesize {filename}"
    client.send(request.encode())

    file_size = int(client.recv(1024).decode())
    client.close()
    return file_size

def download_chunk(filename, start, end, server_ip, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"download {filename} {start} {end}"
    client.send(request.encode())

    data = client.recv(end - start)
    with open(f"{filename}.part{start}", 'wb') as f:
        f.write(data)
    client.close()

def upload_chunk(filename, start, end, server_ip, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"upload {filename} {start} {end}"
    client.send(request.encode())

    with open(filename, 'rb') as f:
        f.seek(start)
        data = f.read(end - start)
        client.sendall(data)
    client.close()

def download_file(filename, server_ip, port, num_threads=4):
    file_size = get_file_size(server_ip, port, filename)
    chunk_size = file_size // num_threads

    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = file_size if i == num_threads - 1 else (i + 1) * chunk_size
        thread = threading.Thread(target=download_chunk, args=(filename, start, end, server_ip, port))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def upload_file(filename, server_ip, port, num_threads=4):
    file_size = os.path.getsize(filename)
    chunk_size = file_size // num_threads

    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = file_size if i == num_threads - 1 else (i + 1) * chunk_size
        thread = threading.Thread(target=upload_chunk, args=(filename, start, end, server_ip, port))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    server_ip = "127.0.0.1"
    port = 12345
    filename = "D:\mmt\large_file.txt"

    # Download file
    download_file(filename, server_ip, port)

    # Upload file
    upload_file(filename, server_ip, port)

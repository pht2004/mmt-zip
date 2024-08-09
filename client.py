import socket
import threading
import os
from tkinter import Tk, Button, Entry, Label, filedialog

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

def download_file(server_ip, port, filename, save_path, num_threads=4):
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

    # Merge the downloaded chunks
    with open(save_path, 'wb') as f:
        for i in range(num_threads):
            part_filename = f"{save_path}.part{i * chunk_size}"
            with open(part_filename, 'rb') as part_file:
                f.write(part_file.read())
            os.remove(part_filename)

def upload_file(server_ip, port, local_path, remote_filename, num_threads=4):
    file_size = os.path.getsize(local_path)
    chunk_size = file_size // num_threads

    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = file_size if i == num_threads - 1 else (i + 1) * chunk_size
        thread = threading.Thread(target=upload_chunk, args=(local_path, start, end, server_ip, port))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Send a request to merge the chunks on the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"merge {remote_filename} {file_size} {num_threads}"
    client.send(request.encode())
    client.close()

def choose_file_upload():
    local_path = filedialog.askopenfilename()
    if local_path:
        remote_filename = os.path.basename(local_path)
        upload_file(server_ip.get(), int(port.get()), local_path, remote_filename)

def choose_file_download():
    filename = input_filename.get()
    save_path = filedialog.asksaveasfilename(defaultextension="*.*", initialfile=filename)
    if filename and save_path:
        download_file(server_ip.get(), int(port.get()), filename, save_path)

# GUI setup
root = Tk()
root.title("Client File Transfer")

Label(root, text="Server IP:").grid(row=0, column=0)
server_ip = Entry(root)
server_ip.grid(row=0, column=1)

Label(root, text="Port:").grid(row=1, column=0)
port = Entry(root)
port.grid(row=1, column=1)
port.insert(0, "12345")

Label(root, text="File Name for Download:").grid(row=2, column=0)
input_filename = Entry(root)
input_filename.grid(row=2, column=1)

Button(root, text="Upload File", command=choose_file_upload).grid(row=3, column=0, pady=10)
Button(root, text="Download File", command=choose_file_download).grid(row=3, column=1, pady=10)

root.mainloop()

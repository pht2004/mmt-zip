import socket
import threading
import os
from tkinter import Tk, Button, Entry, Label, filedialog, messagebox, Listbox

# Function to get the list of files from the server_files directory on the server
def get_file_list(server_ip, port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = "list_files"
    client.send(request.encode())
    file_list = client.recv(4096).decode().split(';')
    client.close()
    return file_list

# Function to get the file size from the server
def get_file_size(server_ip, port, filename):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"filesize {filename}"
    client.send(request.encode())
    file_size = int(client.recv(1024).decode())
    client.close()
    return file_size

# Function to download a chunk of the file from the server
def download_chunk(filename, start, end, server_ip, port, save_path):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"download {filename} {start} {end}"
    client.send(request.encode())

    part_filename = f"{save_path}.part{start}"

    with open(part_filename, 'wb') as f:
        bytes_received = 0
        while bytes_received < (end - start):
            data = client.recv(min(4096, (end - start) - bytes_received))
            if not data:
                break
            f.write(data)
            bytes_received += len(data)

    client.close()

# Function to upload a chunk of the file to the server
def upload_chunk(filename, start, end, server_ip, port, remote_filename):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"upload {remote_filename} {start} {end}"
    client.send(request.encode())

    with open(filename, 'rb') as f:
        f.seek(start)
        bytes_sent = 0
        while bytes_sent < (end - start):
            data = f.read(min(4096, (end - start) - bytes_sent))
            if not data:
                break
            client.sendall(data)
            bytes_sent += len(data)

    client.close()

# Function to calculate the number of threads and chunk size based on file size
def calculate_threads_and_chunk_size(file_size):
    if file_size < 1024:  # Less than 1KB
        num_threads = 1
        chunk_size = file_size
    elif 1024 <= file_size <= 204800:  # Between 1KB and 200KB
        num_threads = 2
        chunk_size = file_size // 2
    elif 204801 <= file_size <= 1048576:  # Between 201KB and 1MB
        num_threads = (file_size + 102399) // 102400  # 100KB per thread
        chunk_size = 102400
    elif 1048577 <= file_size <= 20971520:  # Between 1MB and 20MB
        num_threads = (file_size + 1048575) // 1048576  # 1MB per thread
        chunk_size = 1048576
    else:  # Above 21MB
        num_threads = (file_size + 10485759) // 10485760  # 10MB per thread
        chunk_size = 10485760
    return num_threads, chunk_size

# Function to download a file from the server
def download_file(server_ip, port, filename, save_path):
    file_size = get_file_size(server_ip, port, filename)
    num_threads, chunk_size = calculate_threads_and_chunk_size(file_size)

    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = file_size if i == num_threads - 1 else (i + 1) * chunk_size
        thread = threading.Thread(target=download_chunk, args=(filename, start, end, server_ip, port, save_path))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Merge the parts into the final file
    with open(save_path, 'wb') as f:
        for i in range(num_threads):
            part_filename = f"{save_path}.part{i * chunk_size}"
            with open(part_filename, 'rb') as part_file:
                f.write(part_file.read())
            os.remove(part_filename)

# Function to upload a file to the server
def upload_file(server_ip, port, local_path, remote_filename):
    file_size = os.path.getsize(local_path)
    num_threads, chunk_size = calculate_threads_and_chunk_size(file_size)

    threads = []
    for i in range(num_threads):
        start = i * chunk_size
        end = file_size if i == num_threads - 1 else (i + 1) * chunk_size
        thread = threading.Thread(target=upload_chunk, args=(local_path, start, end, server_ip, port, remote_filename))
        threads.append(thread)
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Notify server to merge parts
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, port))
    request = f"merge {remote_filename} {file_size} {num_threads}"
    client.send(request.encode())
    client.close()

    # Inform the user about the successful upload
    messagebox.showinfo("Success", f"File '{remote_filename}' uploaded successfully!")

# Function to choose a file to upload
def choose_file_upload():
    local_path = filedialog.askopenfilename()
    if local_path:
        remote_filename = os.path.basename(local_path)
        upload_file(server_ip.get(), int(port.get()), local_path, remote_filename)

# Function to choose a file to download
def choose_file_download():
    server_ip_address = server_ip.get()
    server_port = int(port.get())

    # Get the list of files from the server_files directory on the server
    files = get_file_list(server_ip_address, server_port)

    # Display the list of files in a dialog box
    if files:
        download_window = Tk()
        download_window.title("Select File to Download")

        listbox = Listbox(download_window, selectmode='single')
        for file in files:
            listbox.insert('end', file)
        listbox.pack(fill='both', expand=True)

        def select_file():
            selected = listbox.curselection()
            if selected:
                filename = listbox.get(selected)
                # Use filedialog to let the user choose where to save the downloaded file
                save_path = filedialog.asksaveasfilename(defaultextension="", initialfile=filename)
                if save_path:
                    download_file(server_ip_address, server_port, filename, save_path)
                    messagebox.showinfo("Success", f"File '{filename}' downloaded successfully!")
            download_window.destroy()

        Button(download_window, text="Download", command=select_file).pack(pady=10)
        download_window.mainloop()

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

Button(root, text="Upload File", command=choose_file_upload).grid(row=2, column=0, pady=10)
Button(root, text="Download File", command=choose_file_download).grid(row=2, column=1, pady=10)

root.mainloop()

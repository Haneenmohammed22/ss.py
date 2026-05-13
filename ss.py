import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog
from PIL import Image, ImageTk
import io

HOST = '0.0.0.0'
PORT = 50800

client_conn = None

def receive_messages(conn, chat_box):
    while True:
        try:
            header = conn.recv(10).decode().strip()
            if not header: break
            
            size = int(conn.recv(10).decode().strip())
            data = b""
            while len(data) < size:
                packet = conn.recv(size - len(data))
                if not packet: break
                data += packet

            if header == "TEXT":
                show_message(chat_box, f"Client: {data.decode()}")
            elif header == "IMG":
                show_image(chat_box, data, "Client")
        except:
            show_message(chat_box, "[System] Connection lost.")
            break

# دالة إرسال الصورة (نفس منطق الكلاينت)
def send_image(chat_box):
    global client_conn
    file_path = filedialog.askopenfilename()
    if file_path and client_conn:
        with open(file_path, "rb") as f:
            img_data = f.read()
        client_conn.sendall(f"{'IMG':<10}{len(img_data):<10}".encode() + img_data)
        show_image(chat_box, img_data, "You")

def send_message(entry, chat_box):
    global client_conn
    msg = entry.get().strip()
    if msg and client_conn:
        data = msg.encode()
        client_conn.sendall(f"{'TEXT':<10}{len(data):<10}".encode() + data)
        show_message(chat_box, f"You: {msg}")
        entry.delete(0, tk.END)

def show_image(chat_box, data, sender):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"{sender} sent an image:\n")
    img = Image.open(io.BytesIO(data))
    img.thumbnail((200, 200))
    photo = ImageTk.PhotoImage(img)
    label = tk.Label(chat_box, image=photo, bg="#2a2a3d")
    label.image = photo
    chat_box.window_create(tk.END, window=label)
    chat_box.insert(tk.END, "\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)

def show_message(chat_box, msg):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, msg + "\n")
    chat_box.config(state=tk.DISABLED)

def start_server(chat_box):
    def run():
        global client_conn
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        show_message(chat_box, f"[System] Server listening on {PORT}")
        conn, addr = server_socket.accept()
        client_conn = conn
        show_message(chat_box, f"[System] Connected: {addr}")
        threading.Thread(target=receive_messages, args=(conn, chat_box), daemon=True).start()
    threading.Thread(target=run, daemon=True).start()

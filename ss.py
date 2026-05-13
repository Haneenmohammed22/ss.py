import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk
import io
import struct
import os

HOST = '0.0.0.0'
PORT = 50000

client_conn = None
photo_refs = []

# ── Protocol helpers ────────────────────────────────────────────────────────
def send_raw(sock, type_flag: bytes, payload: bytes):
    header = type_flag + struct.pack(">Q", len(payload))
    sock.sendall(header + payload)

def recv_exact(sock, n):
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed")
        buf += chunk
    return buf

def recv_frame(sock):
    header = recv_exact(sock, 12)
    type_flag = header[:4]
    length = struct.unpack(">Q", header[4:])[0]
    payload = recv_exact(sock, length)
    return type_flag, payload

# ── UI helpers ───────────────────────────────────────────────────────────────
def show_message(chat_box, msg):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, msg + "\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)

def show_image(chat_box, img_bytes, label="Client"):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        img.thumbnail((300, 300))
        photo = ImageTk.PhotoImage(img)
        photo_refs.append(photo)

        chat_box.config(state=tk.NORMAL)
        chat_box.insert(tk.END, f"{label} sent a photo:\n")
        chat_box.image_create(tk.END, image=photo)
        chat_box.insert(tk.END, "\n")
        chat_box.yview(tk.END)
        chat_box.config(state=tk.DISABLED)
    except Exception as e:
        show_message(chat_box, f"[System] Could not display image: {e}")

# ── Network ──────────────────────────────────────────────────────────────────
def receive_messages(conn, chat_box):
    while True:
        try:
            type_flag, payload = recv_frame(conn)
            if type_flag == b'MSG\x00':
                show_message(chat_box, f"Client: {payload.decode()}")
            elif type_flag == b'IMG\x00':
                show_image(chat_box, payload, label="Client")
        except Exception as e:
            show_message(chat_box, f"[System] Connection lost: {e}")
            break

def send_message(entry, chat_box):
    global client_conn
    msg = entry.get().strip()
    if msg and client_conn:
        try:
            send_raw(client_conn, b'MSG\x00', msg.encode())
            show_message(chat_box, f"You: {msg}")
            entry.delete(0, tk.END)
        except Exception as e:
            show_message(chat_box, f"[System] Failed to send: {e}")

def send_photo(chat_box):
    global client_conn
    if not client_conn:
        messagebox.showwarning("No client", "No client connected yet.")
        return
    path = filedialog.askopenfilename(
        title="Select a photo",
        filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"), ("All files", "*.*")]
    )
    if not path:
        return
    try:
        with open(path, "rb") as f:
            data = f.read()
        send_raw(client_conn, b'IMG\x00', data)
        show_image(chat_box, data, label=f"You ({os.path.basename(path)})")
    except Exception as e:
        show_message(chat_box, f"[System] Failed to send photo: {e}")

def start_server(chat_box):
    global client_conn
    def run():
        global client_conn
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        show_message(chat_box, f"[System] Server listening on port {PORT}...")
        conn, addr = server_socket.accept()
        client_conn = conn
        show_message(chat_box, f"[System] Connected: {addr}")
        threading.Thread(target=receive_messages, args=(conn, chat_box), daemon=True).start()
    threading.Thread(target=run, daemon=True).start()

                      font=("Consolas", 13), bd=0, relief=tk.FLAT,
                      padx=10, command=lambda: send_photo(chat_box))
photo_btn.pack(side=tk.RIGHT, padx=(0, 5))

send_btn = tk.Button(frame, text="Send", bg="#5865f2", fg="white",
                     font=("Consolas", 11, "bold"), bd=0, relief=tk.FLAT,
                     padx=12, command=lambda: send_message(entry, chat_box))
send_btn.pack(side=tk.RIGHT)

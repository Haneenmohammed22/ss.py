
# =========================
# SERVER.py
# =========================

import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog
import os

HOST = '0.0.0.0'

PORT = int(os.environ.get("PORT", 50000))

client_conn = None


def show_message(chat_box, msg):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, msg + "\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)


def receive_messages(conn, chat_box):

    while True:

        try:
            header = conn.recv(1024)

            if not header:
                show_message(chat_box, "[System] Client disconnected.")
                break

            header = header.decode().strip()

            # استقبال ملف
            if header.startswith("FILE:"):

                _, filename, filesize = header.split(":")
                filesize = int(filesize)

                received = b""

                while len(received) < filesize:

                    chunk = conn.recv(4096)

                    if not chunk:
                        break

                    received += chunk

                save_path = f"received_{filename}"

                with open(save_path, "wb") as f:
                    f.write(received)

                show_message(chat_box, f"[File Received] {filename}")

            # استقبال رسالة عادية
            else:
                show_message(chat_box, f"Client: {header}")

        except Exception as e:
            show_message(chat_box, f"[System] Connection lost: {e}")
            break


def send_message(entry, chat_box):
    global client_conn

    msg = entry.get().strip()

    if msg and client_conn:

        try:
            client_conn.sendall(msg.encode())

            show_message(chat_box, f"You: {msg}")

            entry.delete(0, tk.END)

        except:
            show_message(chat_box, "[System] Failed to send message.")


def send_file(chat_box):
    global client_conn

    file_path = filedialog.askopenfilename(
        filetypes=[
            ("Images", "*.png *.jpg *.jpeg"),
            ("Videos", "*.mp4 *.avi *.mov"),
            ("All Files", "*.*")
        ]
    )

    if not file_path:
        return

    try:
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()

        header = f"FILE:{filename}:{len(file_data)}"

        # إرسال الهيدر
        client_conn.send(header.encode().ljust(1024))

        # إرسال الملف
        client_conn.sendall(file_data)

        show_message(chat_box, f"[File Sent] {filename}")

    except Exception as e:
        show_message(chat_box, f"[Error] {e}")


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

        t = threading.Thread(
            target=receive_messages,
            args=(conn, chat_box),
            daemon=True
        )

        t.start()

    threading.Thread(target=run, daemon=True).start()


# =========================
# UI
# =========================

root = tk.Tk()

root.title("Chat Server")

root.geometry("500x600")

root.configure(bg="#1e1e2e")

chat_box = scrolledtext.ScrolledText(
    root,
    state=tk.DISABLED,
    bg="#2a2a3d",
    fg="#e0e0e0",
    font=("Consolas", 11),
    bd=0
)

chat_box.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=True)

frame = tk.Frame(root, bg="#1e1e2e")

frame.pack(fill=tk.X, padx=10, pady=(0, 10))

entry = tk.Entry(
    frame,
    font=("Consolas", 11),
    bg="#2a2a3d",
    fg="white",
    insertbackground="white",
    bd=0
)

entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))

entry.bind("<Return>", lambda e: send_message(entry, chat_box))

send_btn = tk.Button(
    frame,
    text="Send",
    bg="#5865f2",
    fg="white",
    font=("Consolas", 11, "bold"),
    bd=0,
    padx=12,
    command=lambda: send_message(entry, chat_box)
)

send_btn.pack(side=tk.RIGHT)

file_btn = tk.Button(
    frame,
    text="File",
    bg="#43b581",
    fg="white",
    font=("Consolas", 11, "bold"),
    bd=0,
    padx=12,
    command=lambda: send_file(chat_box)
)

file_btn.pack(side=tk.RIGHT, padx=5)

start_server(chat_box)

root.mainloop()


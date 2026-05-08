import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog
import os
from PIL import Image, ImageTk

HOST = '0.0.0.0' 
PORT = 50000

client_conn = None
img_refs = []  # لمنع حذف الصور من ذاكرة البرنامج

def show_message(chat_box, msg, is_image=False, img_path=None):
    chat_box.config(state=tk.NORMAL)
    if is_image and img_path:
        try:
            img = Image.open(img_path)
            img.thumbnail((200, 200))
            photo = ImageTk.PhotoImage(img)
            img_refs.append(photo)
            chat_box.image_create(tk.END, image=photo)
            chat_box.insert(tk.END, "\n")
        except:
            chat_box.insert(tk.END, "[System] Error displaying image.\n")
    else:
        chat_box.insert(tk.END, msg + "\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)

def receive_messages(conn, chat_box):
    while True:
        try:
            header = conn.recv(1024).decode().strip()
            if not header: break

            if header.startswith("MSG:"):
                msg_content = header[4:]
                show_message(chat_box, f"Client: {msg_content}")
            
            elif header.startswith("FILE:"):
                _, filename, filesize = header.split(":")
                filesize = int(filesize)
                save_path = f"server_received_{filename}"
                
                with open(save_path, "wb") as f:
                    remaining = filesize
                    while remaining > 0:
                        chunk = conn.recv(min(remaining, 4096))
                        if not chunk: break
                        f.write(chunk)
                        remaining -= len(chunk)
                
                show_message(chat_box, f"Client sent a file: {filename}")
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    show_message(chat_box, "", is_image=True, img_path=save_path)
        except:
            break

def send_text(entry, chat_box):
    global client_conn
    msg = entry.get().strip()
    if msg and client_conn:
        try:
            header = f"MSG:{msg}".ljust(1024)
            client_conn.sendall(header.encode())
            show_message(chat_box, f"You: {msg}")
            entry.delete(0, tk.END)
        except:
            show_message(chat_box, "[System] Error sending.")

def send_file(chat_box):
    global client_conn
    if not client_conn: return
    path = filedialog.askopenfilename()
    if not path: return
    try:
        filename = os.path.basename(path)
        filesize = os.path.getsize(path)
        header = f"FILE:{filename}:{filesize}".ljust(1024)
        client_conn.sendall(header.encode())
        with open(path, "rb") as f:
            while chunk := f.read(4096):
                client_conn.sendall(chunk)
        show_message(chat_box, f"You sent: {filename}")
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            show_message(chat_box, "", is_image=True, img_path=path)
    except:
        show_message(chat_box, "[System] File send failed.")

def start_server(chat_box):
    def run():
        global client_conn
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.listen(1)
        show_message(chat_box, f"[System] Server listening on {PORT}...")
        conn, addr = s.accept()
        client_conn = conn
        show_message(chat_box, f"[System] Connected to {addr}")
        threading.Thread(target=receive_messages, args=(conn, chat_box), daemon=True).start()
    threading.Thread(target=run, daemon=True).start()

# UI Setup (نفس التصميم السابق مع إضافة زر File)
root = tk.Tk()
root.title("Chat Server")
root.geometry("400x500")
root.configure(bg="#1e1e2e")
chat_box = scrolledtext.ScrolledText(root, state=tk.DISABLED, bg="#2a2a3d", fg="white")
chat_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
entry = tk.Entry(root, bg="#2a2a3d", fg="white")
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)
entry.bind("<Return>", lambda e: send_text(entry, chat_box))
tk.Button(root, text="Send", command=lambda: send_text(entry, chat_box)).pack(side=tk.RIGHT, padx=5)
tk.Button(root, text="File", command=lambda: send_file(chat_box)).pack(side=tk.RIGHT)

start_server(chat_box)
root.mainloop()

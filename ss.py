import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import os

# ========================

# ========================
HOST = '0.0.0.0'  
PORT = 50000

client_conn = None  
ALLOWED_EXTENSIONS = (
    # صور
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff',
    # فيديو
    '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.3gp'
)

SAVE_DIR = "received_files"
os.makedirs(SAVE_DIR, exist_ok=True)


def receive_messages(conn, chat_box):
   
    buffer = b""
    receiving_file = False
    file_name = ""
    file_size = 0
    file_data = b""

    while True:
        try:
            chunk = conn.recv(4096)
            if not chunk:
                show_message(chat_box, "[System] Client disconnected.")
                break

            buffer += chunk

            while buffer:
                if not receiving_file:
                    if len(buffer) < 1024:
                        break
                    header_bytes = buffer[:1024]
                    header = header_bytes.decode(errors='ignore').strip()

                    if header.startswith("FILE:"):
                        parts = header.split(":")
                        if len(parts) >= 3:
                            file_name = parts[1]
                            file_size = int(parts[2])
                            receiving_file = True
                            file_data = b""
                            buffer = buffer[1024:]
                    else:
                        # رسالة نصية عادية
                        newline_idx = header_bytes.find(b'\n')
                        if newline_idx == -1:
                            msg = header_bytes.decode(errors='ignore').strip()
                            buffer = buffer[1024:]
                        else:
                            msg = buffer[:newline_idx].decode(errors='ignore').strip()
                            buffer = buffer[newline_idx + 1:]
                        if msg:
                            show_message(chat_box, f"Client: {msg}")
                else:
                    # بنستقبل بيانات الملف
                    needed = file_size - len(file_data)
                    file_data += buffer[:needed]
                    buffer = buffer[needed:]

                    if len(file_data) >= file_size:
                        save_path = os.path.join(SAVE_DIR, file_name)
                        with open(save_path, "wb") as f:
                            f.write(file_data)
                        show_message(chat_box, f"[File Received] {file_name} → saved to '{SAVE_DIR}/'")
                        receiving_file = False
                        file_name = ""
                        file_size = 0
                        file_data = b""

        except Exception as e:
            show_message(chat_box, f"[System] Connection lost: {e}")
            break


def send_message(entry, chat_box):
    """ترسل الرسالة للكلاينت"""
    global client_conn
    msg = entry.get().strip()
    if msg and client_conn:
        try:
            client_conn.sendall((msg + "\n").encode())
            show_message(chat_box, f"You: {msg}")
            entry.delete(0, tk.END)
        except:
            show_message(chat_box, "[System] Failed to send message.")


def send_file(chat_box):
    global client_conn

    if not client_conn:
        show_message(chat_box, "[System] No client connected yet.")
        return

    file_path = filedialog.askopenfilename(
        title="Select Photo or Video",
        filetypes=[
            ("Photos & Videos",
             "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff "
             "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm *.3gp"),
            ("All files", "*.*")
        ]
    )

    if not file_path:
        return

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        messagebox.showerror("Not Allowed", f"Only photos and videos are supported.\nFile type '{ext}' is not allowed.")
        return

    try:
        filename = os.path.basename(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()

        header = f"FILE:{filename}:{len(file_data)}"
        client_conn.send(header.encode().ljust(1024))   # ✅ تم تصحيح client_socket → client_conn
        client_conn.sendall(file_data)

        show_message(chat_box, f"[File Sent] {filename} ({len(file_data):,} bytes)")

    except Exception as e:
        show_message(chat_box, f"[Error] {e}")


def show_message(chat_box, msg):
    
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, msg + "\n")
    chat_box.yview(tk.END)
    chat_box.config(state=tk.DISABLED)


def start_server(chat_box):
    """يشغّل السيرفر في thread مستقل"""
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

        t = threading.Thread(target=receive_messages, args=(conn, chat_box), daemon=True)
        t.start()

    threading.Thread(target=run, daemon=True).start()


# ========================
# الـ UI
# ========================
root = tk.Tk()
root.title("Chat Server")
root.geometry("500x600")
root.resizable(False, False)
root.configure(bg="#1e1e2e")

chat_box = scrolledtext.ScrolledText(root, state=tk.DISABLED, wrap=tk.WORD,
                                      bg="#2a2a3d", fg="#e0e0e0",
                                      font=("Consolas", 11), bd=0)
chat_box.pack(padx=10, pady=(10, 5), fill=tk.BOTH, expand=True)

frame = tk.Frame(root, bg="#1e1e2e")
frame.pack(fill=tk.X, padx=10, pady=(0, 10))

entry = tk.Entry(frame, font=("Consolas", 11), bg="#2a2a3d", fg="white",
                 insertbackground="white", bd=0, relief=tk.FLAT)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 5))
entry.bind("<Return>", lambda e: send_message(entry, chat_box))

file_btn = tk.Button(frame, text="📎 Photo/Video",
                     bg="#43b581", fg="white",
                     font=("Consolas", 10, "bold"),
                     bd=0, padx=10,
                     command=lambda: send_file(chat_box))
file_btn.pack(side=tk.RIGHT, padx=5)

send_btn = tk.Button(frame, text="Send", bg="#5865f2", fg="white",
                     font=("Consolas", 11, "bold"), bd=0, relief=tk.FLAT,
                     padx=12, command=lambda: send_message(entry, chat_box))
send_btn.pack(side=tk.RIGHT)

# ابدأ السيرفر تلقائياً
start_server(chat_box)

root.mainloop()

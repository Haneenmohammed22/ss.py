import socket
import threading
import os

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 50000))

clients = []


def broadcast(sender_conn, data):
    for client in clients:
        if client != sender_conn:
            try:
                client.sendall(data)
            except:
                pass


def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr}")

    while True:
        try:
            header = conn.recv(10)

            if not header:
                break

            msg_type = header.decode().strip()

            size_data = conn.recv(10)

            if not size_data:
                break

            size = int(size_data.decode().strip())

            data = b""

            while len(data) < size:
                packet = conn.recv(size - len(data))

                if not packet:
                    break

                data += packet

            full_message = header + size_data + data

            if msg_type == "TEXT":
                print(f"[TEXT] {addr}: {data.decode(errors='ignore')}")

            elif msg_type == "IMG":
                print(f"[IMAGE] {addr} sent image ({size} bytes)")

            broadcast(conn, full_message)

        except Exception as e:
            print(f"[ERROR] {addr}: {e}")
            break

    print(f"[DISCONNECTED] {addr}")

    if conn in clients:
        clients.remove(conn)

    conn.close()


def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))

    server_socket.listen()

    print(f"[LISTENING] Server running on port {PORT}")

    while True:
        conn, addr = server_socket.accept()

        clients.append(conn)

        thread = threading.Thread(
            target=handle_client,
            args=(conn, addr),
            daemon=True
        )

        thread.start()


if __name__ == "__main__":
    start_server()

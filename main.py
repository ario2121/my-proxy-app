import flet as ft
import socket, threading, time

class FragmentProxy:
    def __init__(self):
        self.is_running = False
        self.server_socket = None
        self.listen_port = 2500

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('127.0.0.1', self.listen_port))
        self.server_socket.listen(128)
        self.is_running = True
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                client_sock, _ = self.server_socket.accept()
                threading.Thread(target=self.handle, args=(client_sock,), daemon=True).start()
            except: continue

    def handle(self, client_sock):
        backend_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            data = client_sock.recv(16384)
            if data:
                backend_sock.connect(('172.64.146.0', 443))
                threading.Thread(target=self.forward, args=(backend_sock, client_sock), daemon=True).start()
                # Fragmentation logic
                for i in range(0, len(data), 77):
                    backend_sock.sendall(data[i:i+77])
                    time.sleep(0.2)
                while self.is_running:
                    data = client_sock.recv(4096)
                    if not data: break
                    backend_sock.sendall(data)
        except: pass
        finally:
            client_sock.close()
            backend_sock.close()

    def forward(self, source, dest):
        try:
            while self.is_running:
                data = source.recv(16384)
                if not data: break
                dest.sendall(data)
        except: pass

proxy = FragmentProxy()

def main(page: ft.Page):
    page.title = "Proxy Toggle"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    status = ft.Text("OFF 🔴", size=40, color=ft.Colors.RED)
    
    def on_click(e):
        if not proxy.is_running:
            threading.Thread(target=proxy.start, daemon=True).start()
            status.value = "ON 🟢"
            status.color = ft.Colors.GREEN
            btn.text = "STOP"
            btn.bgcolor = ft.Colors.RED_700
        else:
            proxy.is_running = False
            proxy.server_socket.close()
            status.value = "OFF 🔴"
            status.color = ft.Colors.RED
            btn.text = "START"
            btn.bgcolor = ft.Colors.GREEN_700
        page.update()

    btn = ft.ElevatedButton("START", on_click=on_click, width=200, height=80, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE)
    page.add(status, ft.Text("Port: 2500"), ft.Divider(height=20), btn)

ft.app(target=main)
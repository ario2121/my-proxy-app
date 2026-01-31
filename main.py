import flet as ft
import socket
import threading
import time

class ProxyManager:
    def __init__(self):
        self.is_running = False
        self.port = 2080 # پورت جدید و باز
        self.server_sock = None

    def start_proxy(self):
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(('127.0.0.1', self.port))
            self.server_sock.listen(50)
            self.is_running = True
            
            while self.is_running:
                try:
                    self.server_sock.settimeout(1.0)
                    client, _ = self.server_sock.accept()
                    threading.Thread(target=self.handle, args=(client,), daemon=True).start()
                except:
                    continue
        except:
            self.is_running = False

    def handle(self, client):
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            backend.settimeout(15)
            data = client.recv(16384)
            if not data: return
            
            backend.connect(('172.64.146.0', 443))
            
            # ارسال تکه تکه (Fragment)
            for i in range(0, len(data), 77):
                backend.sendall(data[i:i+77])
                time.sleep(0.1)
            
            # انتقال دو طرفه ساده
            def forward(src, dst):
                try:
                    while self.is_running:
                        buf = src.recv(16384)
                        if not buf: break
                        dst.sendall(buf)
                except: pass

            threading.Thread(target=forward, args=(backend, client), daemon=True).start()
            forward(client, backend)
        except: pass
        finally:
            try:
                client.close()
                backend.close()
            except: pass

proxy = ProxyManager()

def main(page: ft.Page):
    page.title = "Simple Proxy"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    status = ft.Text("متوقف شده 🔴", size=30)
    
    def toggle(e):
        if not proxy.is_running:
            threading.Thread(target=proxy.start_proxy, daemon=True).start()
            status.value = "در حال کار 🟢"
            status.color = ft.colors.GREEN
            btn.text = "STOP"
            btn.bgcolor = ft.colors.RED
        else:
            proxy.is_running = False
            if proxy.server_sock:
                proxy.server_sock.close()
            status.value = "متوقف شده 🔴"
            status.color = ft.colors.WHITE
            btn.text = "START"
            btn.bgcolor = ft.colors.GREEN
        page.update()

    btn = ft.ElevatedButton("START", on_click=toggle, width=200, height=60, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE)
    
    page.add(
        ft.Text("Fragment Proxy", size=25, weight="bold"),
        ft.Text(f"Port: {proxy.port}"),
        ft.Divider(height=30),
        status,
        ft.Container(height=20),
        btn
    )

if __name__ == "__main__":
    ft.app(target=main)
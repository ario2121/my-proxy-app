import flet as ft
import socket
import threading
import time
from datetime import datetime

class ProxyEngine:
    def __init__(self, log_callback):
        self.is_running = False
        self.port = 2080
        self.server_sock = None
        self.log_callback = log_callback

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_callback(f"[{timestamp}] {message}")

    def start(self):
        try:
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_sock.bind(('127.0.0.1', self.port))
            self.server_sock.listen(50)
            self.is_running = True
            self.log(f"Server started on port {self.port}")
            
            while self.is_running:
                try:
                    self.server_sock.settimeout(1.0)
                    client, addr = self.server_sock.accept()
                    self.log(f"Connection from {addr[0]}")
                    threading.Thread(target=self.handle, args=(client, addr), daemon=True).start()
                except socket.timeout:
                    continue
                except:
                    break
        except Exception as e:
            self.log(f"Start Error: {str(e)}")
            self.is_running = False

    def handle(self, client, addr):
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            backend.settimeout(10)
            data = client.recv(16384)
            if not data: 
                client.close()
                return
            
            backend.connect(('172.64.146.0', 443))
            
            # ارسال فرگمنت‌ها
            self.log(f"Sending fragments to CF...")
            for i in range(0, len(data), 77):
                if not self.is_running: break
                backend.sendall(data[i:i+77])
                time.sleep(0.1)
            
            self.log(f"Handshake done for {addr[0]}")

            def forward(src, dst):
                try:
                    while self.is_running:
                        buf = src.recv(16384)
                        if not buf: break
                        dst.sendall(buf)
                except: pass

            threading.Thread(target=forward, args=(backend, client), daemon=True).start()
            forward(client, backend)
        except Exception as e:
            self.log(f"Pipe Error: {str(e)}")
        finally:
            try:
                client.close()
                backend.close()
                self.log(f"Closed: {addr[0]}")
            except: pass

def main(page: ft.Page):
    page.title = "Proxy with Logs"
    page.theme_mode = "dark"
    page.padding = 20
    
    # لیست برای نگهداری لاگ‌ها در UI
    log_column = ft.Column(scroll="always", expand=True)
    
    def add_log(message):
        log_column.controls.append(ft.Text(message, size=12, font_family="monospace"))
        # نگه داشتن فقط ۵۰ لاگ آخر برای جلوگیری از سنگین شدن برنامه
        if len(log_column.controls) > 50:
            log_column.controls.pop(0)
        page.update()
        # اسکرول خودکار به انتهای لیست
        log_column.scroll_to(offset=-1, duration=100)

    engine = ProxyEngine(add_log)

    status_text = ft.Text("READY", size=20, color="white", weight="bold")

    def toggle(e):
        if not engine.is_running:
            threading.Thread(target=engine.start, daemon=True).start()
            status_text.value = "RUNNING (ON)"
            status_text.color = "green"
            btn.text = "STOP"
            btn.bgcolor = "red"
        else:
            engine.is_running = False
            if engine.server_sock:
                engine.server_sock.close()
            status_text.value = "STOPPED (OFF)"
            status_text.color = "red"
            btn.text = "START"
            btn.bgcolor = "blue"
        page.update()

    btn = ft.ElevatedButton(
        text="START",
        width=page.window_width,
        height=50,
        on_click=toggle,
        bgcolor="blue",
        color="white"
    )

    # بخش نمایش لاگ‌ها (شبیه ترمینال)
    log_container = ft.Container(
        content=log_column,
        bgcolor="black",
        padding=10,
        border_radius=10,
        border=ft.border.all(1, "grey700"),
        expand=True, # این باعث میشه بقیه فضای صفحه رو بگیره
    )

    page.add(
        ft.Text("Fragment Proxy Control", size=22, weight="bold"),
        ft.Row([status_text, ft.Text(f"Port: {engine.port}", size=14)], alignment="spaceBetween"),
        ft.Divider(),
        btn,
        ft.Text("Live Logs:", size=14, weight="bold"),
        log_container
    )

if __name__ == "__main__":
    ft.app(target=main)

import flet as ft
import socket
import threading
import time

# منطق پروکسی در یک کلاس جداگانه برای جلوگیری از فریز شدن UI
class ProxyEngine:
    def __init__(self):
        self.is_running = False
        self.port = 2080
        self.server_sock = None

    def start(self):
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
            
            for i in range(0, len(data), 77):
                backend.sendall(data[i:i+77])
                time.sleep(0.1)
            
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

engine = ProxyEngine()

def main(page: ft.Page):
    # تنظیمات اولیه صفحه برای جلوگیری از صفحه سیاه
    page.title = "Proxy App"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 50

    status_icon = ft.Icon(ft.icons.SHIELD_OUTLINED, color=ft.colors.RED, size=100)
    status_text = ft.Text("OFF", size=30, weight="bold", color=ft.colors.RED)
    
    def on_click(e):
        if not engine.is_running:
            threading.Thread(target=engine.start, daemon=True).start()
            engine.is_running = True # Force state for UI
            status_text.value = "ON"
            status_text.color = ft.colors.GREEN
            status_icon.icon = ft.icons.SHIELD_ROUNDED
            status_icon.color = ft.colors.GREEN
            btn.text = "STOP"
            btn.bgcolor = ft.colors.RED_ACCENT_700
        else:
            engine.is_running = False
            if engine.server_sock:
                engine.server_sock.close()
            status_text.value = "OFF"
            status_text.color = ft.colors.RED
            status_icon.icon = ft.icons.SHIELD_OUTLINED
            status_icon.color = ft.colors.RED
            btn.text = "START"
            btn.bgcolor = ft.colors.BLUE_700
        page.update()

    btn = ft.ElevatedButton(
        text="START",
        width=200,
        height=60,
        bgcolor=ft.colors.BLUE_700,
        color=ft.colors.WHITE,
        on_click=on_click
    )

    # اضافه کردن المان‌ها به صفحه
    page.add(
        status_icon,
        status_text,
        ft.Text(f"Port: {engine.port}", size=16),
        ft.Container(height=40),
        btn
    )
    page.update()

# بسیار مهم برای اندروید
if __name__ == "__main__":
    ft.app(target=main)
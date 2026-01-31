import flet as ft
import socket
import threading
import time
import traceback

# کلاس پروکسی
class ProxyEngine:
    def __init__(self):
        self.is_running = False
        self.port = 2080

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
                except: continue
        except Exception as e:
            self.error_msg = str(e)

    def handle(self, client):
        backend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            backend.settimeout(10)
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
            client.close()
            backend.close()

engine = ProxyEngine()

def main(page: ft.Page):
    try:
        page.title = "Proxy Debug"
        page.theme_mode = ft.ThemeMode.DARK
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # المان‌های صفحه
        status_text = ft.Text("برنامه آماده است", size=20)
        
        def on_toggle(e):
            try:
                if not engine.is_running:
                    threading.Thread(target=engine.start, daemon=True).start()
                    status_text.value = "پروکسی روشن شد 🟢"
                    btn.text = "STOP"
                else:
                    engine.is_running = False
                    status_text.value = "پروکسی خاموش شد 🔴"
                    btn.text = "START"
                page.update()
            except Exception as ex:
                page.add(ft.Text(f"Click Error: {str(ex)}", color="red"))

        btn = ft.ElevatedButton("START", on_click=on_toggle, width=200, height=60)
        
        page.add(
            ft.Icon(ft.icons.SETTINGS, size=50),
            status_text,
            ft.Text(f"Port: {engine.port}"),
            btn
        )
        
    except Exception as main_ex:
        # اگر برنامه کرش کرد، خطا را در صفحه نشان بده
        page.add(ft.Text(f"Startup Error:\n{traceback.format_exc()}", color="red", size=12))

if __name__ == "__main__":
    # اجرای منعطف‌تر برای اندروید
    ft.app(target=main)

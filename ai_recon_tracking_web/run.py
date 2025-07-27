import subprocess
import threading
import time
import socket
import webbrowser

def wait_for_server_and_open_browser():
    while True:
        try:
            with socket.create_connection(("127.0.0.1", 8000), timeout=1):
                break
        except OSError:
            time.sleep(0.5)
    webbrowser.open("http://127.0.0.1:8000")

def main():
    threading.Thread(target=wait_for_server_and_open_browser).start()
    subprocess.run(["uvicorn", "app.main:app", "--reload"])

if __name__ == "__main__":
    main()

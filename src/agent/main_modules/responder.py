import socketserver
from pathlib import Path

from utils import logs
from utils.configuration import config


def init(persistent_folder: Path) -> None:
    config.load_config(persistent_folder / "config.ini")
    logs.setup_logging("responder")


class UDPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        if data == "version":
            response = "1"
        else:
            response = "N/A"
        socket.sendto(response.encode("utf-8"), self.client_address)


def main(persistent_folder: Path) -> None:
    init(persistent_folder)
    ip = config.get("responder", "ip", required=False)
    port = config.get("responder", "port", required=False)
    if ip and port:
        logs.warning(f"Starting UDP responder on on {ip}:{port}")
        with socketserver.UDPServer((ip, port), UDPHandler) as server:
            server.serve_forever()
    else:
        logs.warning(
            f"UDP responder (IP and port) is not defined and therefore it's not running."
        )

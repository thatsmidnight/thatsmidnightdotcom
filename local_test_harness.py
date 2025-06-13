# Standard Library
import http.server
import socketserver
import webbrowser
from pathlib import Path
from typing import Optional


def start_test_server(
    port: int = 8000,
    directory: Optional[str] = None,
    open_browser: bool = True,
) -> None:
    """
    Start a local test server for the static website.

    Args:
        port: Port number to serve on
        directory: Directory to serve (defaults to 'src')
        open_browser: Whether to automatically open browser
    """
    if directory is None:
        directory = "src"

    src_path = Path(directory)
    if not src_path.exists():
        raise FileNotFoundError(f"Directory {directory} not found")

    # Change to the source directory
    import os

    original_cwd = Path.cwd()
    os.chdir(src_path)

    try:
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            url = f"http://localhost:{port}"
            print(f"Serving {src_path.absolute()} at {url}")

            if open_browser:
                webbrowser.open(url)

            print("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    start_test_server()

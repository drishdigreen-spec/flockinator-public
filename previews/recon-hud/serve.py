"""Serve the editable preview locally without mixing cached module versions."""

from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import json
from pathlib import Path
from urllib.parse import urlsplit


class PreviewHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, max-age=0")
        super().end_headers()

    def send_head(self):
        # Always send the current file, including when an old tab revalidates a
        # previously cached module with only second-resolution modification time.
        for header in ("If-Modified-Since", "If-None-Match"):
            if header in self.headers:
                del self.headers[header]
        name = urlsplit(self.path).path
        if name in ("/", "/index.html", "/map.html"):
            root = Path(self.directory)
            document = root / ("map.html" if name == "/map.html" else "index.html")
            if document.is_file():
                assets = sorted(p for p in root.iterdir()
                                if p.suffix in (".mjs", ".css") and not p.name.startswith("._"))
                digest = sha256()
                for asset in assets:
                    digest.update(asset.name.encode())
                    digest.update(asset.read_bytes())
                revision = digest.hexdigest()[:16]
                imports = {"/" + p.name: "/" + p.name + "?v=" + revision
                           for p in assets if p.suffix == ".mjs"}
                html = document.read_text()
                # Import maps cover transitive imports; script/link attributes
                # need their own version because they bypass import-map lookup.
                for asset in assets:
                    html = html.replace(f'="{asset.name}"', f'="{asset.name}?v={revision}"')
                import_map = '<script type="importmap">' + json.dumps({"imports": imports}) + '</script>'
                html = html.replace("</head>", import_map + "</head>")
                body = html.encode()
                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return BytesIO(body)
        return super().send_head()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    handler = partial(PreviewHandler, directory=str(Path(__file__).parent))
    with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
        print(f"Flockinator preview: http://127.0.0.1:{server.server_port}/ (cache disabled)", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'IceAlphaHunter is Hunting. Status: Online.')

# Get the PORT from the hosting environment (default to 8080)
port = int(os.environ.get("PORT", 8080))
httpd = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
print(f"✅ Fake Web Server running on port {port}")
httpd.serve_forever()

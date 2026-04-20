import http.server
import socketserver
import os

os.chdir('/app/build')

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", 3000), Handler) as httpd:
    print("Serving at port 3000")
    httpd.serve_forever()

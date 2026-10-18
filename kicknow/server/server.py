#!/usr/bin/env python3
import http.server
import sys

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def run():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    directory = sys.argv[2] if len(sys.argv) > 2 else '.'
    handler = lambda *args, **kwargs: NoCacheHandler(*args, directory=directory, **kwargs)
    server = http.server.ThreadingHTTPServer(('0.0.0.0', port), handler)
    print(f'KickNow Server serving on port {port} (no-cache enabled)')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    run()

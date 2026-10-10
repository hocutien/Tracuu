import http.server, re, sys, urllib.request, urllib.error, os, functools
GOC = sys.argv[1]
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        m = re.match(r'^/vn/(\d+)/(\d+)/(\d+)/(\d+)\.mvt$', self.path)
        g = re.match(r'^/gl/([a-z0-9-]+)/(\d+)/(\d+)/(\d+)\.png$', self.path)
        if not m and not g: return super().do_GET()
        u = ('https://onland.vn/api/diachinh/api/cadastral/datasets/%s/tiles/%s/%s/%s.mvt' % m.groups()) if m else ('https://intercdn.guland.vn/land/%s/%s/%s/%s.png' % g.groups())
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read(); st = 200
        except urllib.error.HTTPError as e:
            b = b''; st = e.code
        except Exception as e:
            b = str(e).encode(); st = 502
        self.send_response(st); self.send_header('Content-Type', 'image/png' if g else 'application/vnd.mapbox-vector-tile')
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('127.0.0.1', 8737), functools.partial(H, directory=GOC)).serve_forever()

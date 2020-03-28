#!/usr/bin/python

import SocketServer, SimpleHTTPServer, argparse, json

parser = argparse.ArgumentParser()
parser.add_argument('--port', '-p', type=int, default=8008)
parser.add_argument('--log-request-body', action='store_true', default=False)
args = parser.parse_args()

class HTTPHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    __not_found = "<body>Not found</body>"

    def do_POST(self):
        body = None
        content_length = self.headers.getheader('content-length')
        if content_length:
            body = self.rfile.read(int(content_length))

        if self.path == '/clientauth':
            if body:
                json_body = json.loads(body)  # just check that json is paresable
                if args.log_request_body:
                    print(body)

                stream_url = json_body.get('url', '')
                if stream_url == '/local/mp4/sample1.mp4/playlist.m3u8':
                    redirect_body = '{"return_code":302, "redirect_location":"http://127.0.0.1:8081/content/blocked.mp4/playlist.m3u8"}'
                    self.send_response(200)
                    self.send_header('Content-Length', len(redirect_body))
                    self.end_headers()
                    self.wfile.write(redirect_body)
                elif stream_url == '/local/mp4/sample2.mp4/playlist.m3u8':
                    response_body = '{"return_code":403}'
                    self.send_response(200)
                    self.send_header('Content-Length', len(response_body))
                    self.end_headers()
                    self.wfile.write(response_body)
                elif stream_url.endswith('/chunks.m3u8') or stream_url.endswith('/chunk.m3u8'):
                    redirect_location = 'http://' + json_body.get('host') + stream_url[:stream_url.rfind('/') + 1] + 'playlist.m3u8'
                    print(redirect_location)
                    redirect_body = '{"return_code":302, "redirect_location":"' + redirect_location + '"}'
                    self.send_response(200)
                    self.send_header('Content-Length', len(redirect_body))
                    self.end_headers()
                    self.wfile.write(redirect_body)
                else:
                    user_agent = json_body.get('user_agent', None)
                    if user_agent == "BlockMe/1.0":
                        self.send_response(403)
                        self.send_header('Content-Length', 0)
                        self.end_headers() # it is enough to send 403 with empty body
                        return

                    referer = json_body.get('referer', None)
                    if referer == "http://block.me":
                        self.send_response(403)
                        self.send_header('Content-Length', 0)
                        self.end_headers() # it is enough to send 403 with empty body
                        return

                    body = '{"return_code":200}'
                    self.send_response(200)
                    self.send_header('Content-Length', len(body))
                    self.end_headers()
                    self.wfile.write(body)
            else:
                self.send_response(403)
                self.send_header('Content-Length', 0)
                self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Content-Length', len(self.__not_found))
            self.end_headers()
            self.wfile.write(self.__not_found)

SocketServer.TCPServer.allow_reuse_address = True
httpd = SocketServer.TCPServer(("", args.port), HTTPHandler)

try:
    httpd.serve_forever()
except KeyboardInterrupt, e:
    pass
finally:
    httpd.socket.close()

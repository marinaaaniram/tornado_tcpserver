import socket

import tornado.gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.httpserver import HTTPServer
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop


class SimpleTcpClient(object):
    def __init__(self, stream):
        self.stream = stream

        self.stream.socket.setsockopt(
            socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.stream.socket.setsockopt(
            socket.IPPROTO_TCP, socket.SO_KEEPALIVE, 1)
        self.stream.set_close_callback(self.on_disconnect)

    @tornado.gen.coroutine
    def on_disconnect(self):
        yield []

    @tornado.gen.coroutine
    def on_connect(self):
        yield self.dispatch_client()

    def log(self, src_name, msg, *args, **kwargs):
        print('[%s] %s' % (src_name, msg.format(*args, **kwargs)))

    @tornado.gen.coroutine
    def dispatch_client(self):
        try:
            is_auth = False
            src_name = ''
            while True:
                message = yield self.stream.read_until(b'\n')
                msg = message.split('::')

                if msg[0] == 'Auth':
                    is_auth = True
                    src_name = msg[1].split('\n')[0]
                elif msg[0] == 'End':
                    is_auth = False
                elif is_auth:
                    msg_key = msg[0].decode('utf-8').strip()
                    msg_value = msg[1].decode('utf-8').strip()

                    self.log(src_name, '%s | %s' % (msg_key, msg_value))

                    # [con.write_message('Yeah!!!') for con in WSHandler.connections]

        except StreamClosedError:
            self.log('Error: ', 'StreamClosedError')


class SimpleTcpServer(TCPServer):
    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        connection = SimpleTcpClient(stream)
        yield connection.on_connect()


class WSHandler(WebSocketHandler):
    connections = set()

    def open(self):
        self.connections.add(self)
        print 'new connection'

    def on_message(self, message):
        pass

    def on_close(self):
        self.connections.remove(self)
        print 'connection closed'


class IndexHandler(RequestHandler):
    def get(self):
        self.render("index.html")


application = Application([
    (r'/', IndexHandler),
    (r'/ws', WSHandler),
])


def main():
    # configuration
    host = 'localhost'
    port = 8008

    # # http server
    http_server = HTTPServer(application)
    http_server.listen(8888)

    # tcp server
    server = SimpleTcpServer()
    server.listen(port, host)
    print("Listening on %s:%d..." % (host, port))

    # infinite loop
    IOLoop.instance().start()


if __name__ == "__main__":
    main()

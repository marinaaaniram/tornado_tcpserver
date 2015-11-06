import socket

import tornado.gen
from tornado.iostream import StreamClosedError
from tornado.tcpserver import TCPServer
from tornado.httpserver import HTTPServer
from tornado.websocket import WebSocketHandler
from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop
from tornado.options import define, options


define('tcp_port', default=5555)
define('http_port', default=8888)
define('host', default='localhost')


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

                if message == 'End\n':
                	is_auth = False
                	continue

                msg = message.split(':: ')

                if msg[0] == 'Auth' and len(msg) > 1:
                	is_auth = True
                	src_name = msg[1].split('\n')[0]
                	continue

                if is_auth and len(msg) > 1:
	                msg_key = msg[0].decode('utf-8').strip()
	                msg_value = msg[1].decode('utf-8').strip()

	                self.log(src_name, '%s | %s' % (msg_key, msg_value))
	                [con.write_message('[%s] %s | %s' % (src_name, msg_key, msg_value)) for con in WSHandler.connections]

        except StreamClosedError:
            self.log('Error', 'StreamClosedError')


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
    # http server
    http_server = HTTPServer(application)
    http_server.listen(options.http_port, options.host)

    # tcp server
    server = SimpleTcpServer()
    server.listen(options.tcp_port, options.host)
    print('Server started...')

    # infinite loop
    IOLoop.instance().start()


if __name__ == "__main__":
    main()

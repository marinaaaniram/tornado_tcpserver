import socket

import tornado.gen
import tornado.ioloop
import tornado.iostream
import tornado.tcpserver


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
            while True:
                auth = yield self.stream.read_until(b'\n')
                src = auth.split('::')

                if src[0] == 'Auth':
                    src_name = src[1].decode('utf-8').strip()

                    msg = yield self.stream.read_until(b'End\n')
                    msg = msg.split('\n')

                    for i in msg:
                        if i == 'End':
                            break
                        msg_key = i.split('::')[0].decode('utf-8').strip()
                        msg_value = i.split('::')[1].decode('utf-8').strip()

                        self.log(src_name, '%s | %s' % (msg_key, msg_value))

        except tornado.iostream.StreamClosedError:
            self.log(src_name, 'StreamClosedError')

class SimpleTcpServer(tornado.tcpserver.TCPServer):

    @tornado.gen.coroutine
    def handle_stream(self, stream, address):
        """
        Called for each new connection, stream.socket is
        a reference to socket object
        """
        connection = SimpleTcpClient(stream)
        yield connection.on_connect()


def main():
    # configuration
    host = 'localhost'
    port = 8008

    # tcp server
    server = SimpleTcpServer()
    server.listen(port, host)
    print("Listening on %s:%d..." % (host, port))

    # infinite loop
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
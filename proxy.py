import logging

import socketserver
import email_utils

from server import Forwarder

__author__ = 'Michael B. McCoy'


logger = logging.getLogger(__name__)

class ProxyServerError(Exception):
    pass


class ParseError(ProxyServerError):
    pass


class TCPProxyHandler(socketserver.ThreadingMixIn,
               socketserver.BaseRequestHandler):
    """
    """
    chunk_size = 4096
    emailer = email_utils.EmailConnection()

    def handle(self):
        logger.debug("%s connected", self.client_address[0])

        # Collect the full request
        data = b''
        while True:
            try:
                data += self.request.recv(self.chunk_size)
            except BlockingIOError:
                break
        logger.debug("%s", data)

        request = Forwarder(data)
        request.forward()

        logger.debug("Recieved response\n%s", request.response)
        for chunk in request.response.iter_content(self.chunk_size):
            self.request.sendall(chunk)


if __name__ == "__main__":
    logger.basicConfig(level=logging.DEBUG)

    HOST, PORT = "localhost", 9999
    logger.debug("Creating proxy server at {}:{}".format(HOST, PORT))

    # Create the server, binding to localhost on port 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TCPProxyHandler)
    logger.debug("Server created.")

    logger.debug("Placing server into nonblocking mode.")
    tcp_server.socket.setblocking(False)
    logger.debug('Done.')

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    logger.debug("Starting server.")
    try:
        tcp_server.serve_forever()
    except KeyboardInterrupt:
        tcp_server.shutdown()
    finally:
        tcp_server.shutdown()

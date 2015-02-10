import email
from email.mime.text import MIMEText
import logging
import smtplib

import socketserver


from server import Forwarder


__author__ = 'Michael B. McCoy'


class ProxyServerError(Exception):
    pass


class ParseError(ProxyServerError):
    pass


class TCPProxyHandler(socketserver.ThreadingMixIn,
               socketserver.BaseRequestHandler):
    """
    """
    chunk_size = 4096

    def handle(self):
        # self.request is the TCP socket connected to the client
        # self.data = self.request.recv(1024).strip()
        logging.debug("%s connected", self.client_address[0])

        # Collect the full request
        data = b''
        while True:
            try:
                data += self.request.recv(self.chunk_size)
            except BlockingIOError:
                break
        logging.debug("%s", data)

        # TODO: Handle 100-continue directives?
        request = Forwarder(data)
        request.forward()

        logging.debug("Recieved response\n%s", request.response)
        for chunk in request.response.iter_content(self.chunk_size):
            self.request.sendall(chunk)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    HOST, PORT = "localhost", 9999
    logging.debug("Creating proxy server at {}:{}".format(HOST, PORT))

    # Create the server, binding to localhost on port 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TCPProxyHandler)
    logging.debug("Server created.")

    logging.debug("Placing server into nonblocking mode.")
    tcp_server.socket.setblocking(False)
    logging.debug('Done.')

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    logging.debug("Starting server.")
    try:
        tcp_server.serve_forever()
    except KeyboardInterrupt:
        tcp_server.shutdown()
    finally:
        tcp_server.shutdown()

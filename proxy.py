from io import BytesIO
import logging

import socket
import socketserver

from http.client import parse_headers

import requests

__author__ = 'Michael B. McCoy'


class ProxyServerError(Exception):
    pass


class ParseError(ProxyServerError):
    pass



class ProxyRequest:

    def __init__(self, raw_request):
        self.raw = raw_request
        self.connection = self.response = None
        self.close_connection = True

        # Parse the raw request into constituents
        CSRF = b'\r\n'
        request_lines = self.raw.split(CSRF)
        request = str(request_lines[0], 'iso-8859-1')
        try:
            self.method, self.path, self.version = request.split()
        except ValueError:
            self.method, self.path = request.split()

        headers = CSRF.join(request_lines[1:])
        self.headers = parse_headers(BytesIO(headers))

    def forward(self):
        """
        Forward request to its destination. Returns a requests.Response object
        """
        logging.debug("path = %s", self.path)
        self.response = requests.request(method=self.method.lower(), url=self.path, headers=self.headers)
        return self.response


class TCPProxy(socketserver.ThreadingMixIn,
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
        request = ProxyRequest(data)
        request.forward()

        logging.debug("Recieved response\n%s", request.response)
        for chunk in request.response.iter_content(self.chunk_size):
            self.request.sendall(chunk)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    HOST, PORT = "localhost", 9999
    logging.debug("Creating server at {}:{}".format(HOST, PORT))

    # Create the server, binding to localhost on port 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TCPProxy)
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

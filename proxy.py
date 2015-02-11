import logging
import smtplib

import imaplib
import socketserver
import getpass

from server import Forwarder

__author__ = 'Michael B. McCoy'


logger = logging.getLogger(__name__)


class ProxyServerError(Exception):
    pass


class ParseError(ProxyServerError):
    pass


class ProxyEmailer(smtplib.SMTP, imaplib.IMAP4):
    """Just a copy of SMTP right now."""

    def __init__(self,
                 smtp_host='localhost', smtp_port=smtplib.SMTP_PORT,
                 imap_host='localhost', imap_port=imaplib.IMAP4_PORT,
                 imap_username=None, imap_password=None,
                 ):

        # Start SMTP server (no authentication)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_server = smtplib.SMTP(smtp_host, smtp_port)

        # Start IMAP server
        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_server = imaplib.IMAP4(imap_host, imap_port)

        # Authenticate IMAP connection:
        self.imap_username = imap_username or getpass.getuser()
        self.imap_password = imap_password or getpass.getpass()
        self.imap_server.login(self.imap_username, self.imap_password)

    def forward(self, data):
        """Forward the data and block until we get a response."""



class TCPProxyHandler(socketserver.ThreadingMixIn,
                      socketserver.BaseRequestHandler):

    chunk_size = 4096

    def __init__(self, host='localhost', port=1111, *args, **kwargs):
        self.emailer = ProxyEmailer(host, port)
        super().__init__(*args, **kwargs)

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

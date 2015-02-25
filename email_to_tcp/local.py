from getpass import getpass
import imaplib
import logging
import smtplib
import socketserver
from io import BytesIO

from email_to_tcp import utils


logger = logging.getLogger(
    'proxy' if __name__ == '__main__' else __name__)

settings = utils.proxy_settings


class TCPProxyHandler(socketserver.BaseRequestHandler):
    chunk_size = 4096
    email_connection = None  # Lazy evaluation necessary here

    def handle(self):
        """Handle the request"""
        if TCPProxyHandler.email_connection is None:
            raise AttributeError(
                "You must call TCPProxyHandler.connect(settings) "
                "before starting the server.")

        logger.debug("%s connected", self.client_address[0])
        data = b''
        while True:
            try:
                data += self.request.recv(self.chunk_size)
            except BlockingIOError:
                break
        logger.debug("%s", data)
        subject = self.email_connection.send(data)

        response = self.email_connection.fetch(subject='Re: ' + subject)
        logger.debug("Received response\n%s", response)
        raw_data = BytesIO(utils.unpack(response))

        while True:
            chunk = raw_data.read(self.chunk_size)
            if not chunk:
                break
            self.request.sendall(chunk)

    @classmethod
    def connect(cls, s):
        cls.email_connection = utils.EmailConnection(s)


def configure(s=utils.proxy_settings):
    if not s.SMTP_SERVER:
        s.SMTP_SERVER = input("Enter the SMTP server that you have local "
                              "access to (ex: smtp.gmail.com): \n")
    if not s.SMTP_USER:
        s.SMTP_USER = input("Your SMTP username (ex: example@gmail.com):\n")
        s.SMTP_USE_SSL = bool(input("Use SSL? [Y/n]").lower() != 'n')
        default_port = s.SMTP_USE_SSL and \
                       smtplib.SMTP_SSL_PORT or smtplib.SMTP_PORT
        s.SMTP_PORT = int(input("Port (default %d): " % default_port)
                          or default_port)

    if not s.SMTP_PASSWORD:
        s.SMTP_PASSWORD = getpass("SMTP password: ")

    if not s.IMAP_SERVER:
        s.IMAP_SERVER = input("Enter the IMAP server that you have "
                              "local access to (ex: imap.gmail.com): \n")

    if not s.IMAP_USER:
        s.IMAP_USER = input("Your IMAP username (default %s): \n"
                            % s.SMTP_USER) or s.SMTP_USER
        s.IMAP_USE_SSL = bool(input("Use SSL? [Y/n]").lower() != 'n')
        default_port = s.IMAP_USE_SSL and \
                       imaplib.IMAP4_SSL_PORT or imaplib.IMAP4_PORT
        s.IMAP_PORT = int(input("Port (default %d): " % default_port)
                          or default_port)

    if not s.IMAP_PASSWORD:
        s.IMAP_PASSWORD = getpass("IMAP password: ")

    s.FROM_EMAIL = s.SMTP_USER

    if not s.TO_EMAIL:
        s.TO_EMAIL = input("Enter the email address that the remote "
                           "server is monitoring: \n")

    s.HOST = '127.0.0.1'
    s.PORT = 9999

    return s


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    settings = configure(settings)
    print("======================================")
    print("Settings: \n{}".format(settings))
    print("======================================")

    HOST, PORT = settings.HOST, settings.PORT
    logger.info("Creating proxy server at {}:{}".format(HOST, PORT))

    TCPProxyHandler.connect(settings)

    # Create the server, binding to localhost on port 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TCPProxyHandler)
    logger.debug("Server created.")

    logger.debug("Placing server into non-blocking mode.")
    tcp_server.socket.setblocking(False)

    logger.info("Starting server... (stop with Ctrl-C)")
    try:
        tcp_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tcp_server.shutdown()

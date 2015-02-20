import logging
import smtplib

import imaplib2
import socketserver

import email

import petname

from configure import proxy_settings
import email_utils
from remote import Forwarder

__author__ = 'Michael B. McCoy'

logger = logging.getLogger(
    'proxy' if __name__ == '__main__' else __name__)


# Exceptions
class ProxyServerError(Exception):
    pass


class ParseError(ProxyServerError):
    pass


class SMTPError(ProxyServerError):
    pass


class EmailConnection:
    """Houses both an SMTP and IMAP connection for bidirectional packet
    communication through email. This class takes care of sending and
    receiving the responses from the email server, packaging up the
    data to send, etc.
    """

    def __init__(self, settings=proxy_settings):

        self.from_email = settings.FROM_EMAIL
        self.to_email = settings.TO_EMAIL

        logger.debug("Starting SMTP server...")
        if settings.SMTP_USE_SSL:
            self.smtp = smtplib.SMTP_SSL(settings.SMTP_SERVER,
                                         settings.SMTP_PORT)
        else:
            self.smtp = smtplib.SMTP(settings.SMTP_SERVER,
                                     settings.SMTP_PORT)

        # TODO(?): Handle non-auth SMTP. (Open relays are rare...)
        self.smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        logger.debug("Starting IMAP server...")
        if settings.IMAP_USE_SSL:
            self.imap = imaplib2.IMAP4_SSL(settings.IMAP_SERVER,
                                                 settings.IMAP_PORT)
        else:
            self.imap = imaplib2.IMAP4(settings.IMAP_SERVER,
                                             settings.IMAP_PORT)
        self.imap.login(settings.IMAP_USER,
                               settings.IMAP_PASSWORD)
        self.imap.select("Inbox")  # TODO: Allow other inboxes

        # TODO: Chekc if IDLE is allowed, and if not, revert to polling (ugh)

    def forward(self, data):
        """Forward the data and block until we get a response"""

        subject = petname.Generate(3, ' ')
        package = email_utils.pack(self.from_email, [self.to_email],
                                   subject, data)

        logging.debug("Sending message: %s", package.as_string())
        self.smtp.sendmail(self.from_email, [self.to_email], package.as_string())

        return self._get_response(subject)

    def _get_response(self, subject):
        """Fetch the email response corresponding to a specific request

        Algorithm overview:
         1. Make an IMAP IDLE call.
         2. When the idle breaks or timeouts, check if there is a
         message with whose subject line contains the 'subject'
         argument.
         3. If not, go back to IDLE (step 1).
         4. Otherwise, unpack the data from the message and return.
        """

        # TODO Timeout implementation
        # TODO Implement something other than IDLE?
        while True:
            logger.debug("Waiting for IDLE to break....")
            status, message = self.imap.idle(timeout=5)
            logger.debug("IDLE broken: %s : %s", status, message)

            # See if we've got the reply
            status, search_results = self.imap.uid('search', None,
                                                   "TEXT", subject)
            logger.debug("Search results %s : %s", status, search_results)
            if search_results[0]:
                break
        unique_ids = search_results[0].split()
        if len(unique_ids) > 1:
            logger.warn("Too many responses from search query SUBJECT %s", subject)

        # Get the most recent message
        status, raw_data = self.imap.uid("fetch", unique_ids[-1], '(RFC822)')
        logger.debug("Response STATUS: %s\nDATA: %s", status, raw_data)
        response_email = email.message_from_string(raw_data[0][1])

        # TODO: Stop faking this:
        raw_data = email_utils.unpack(response_email)
        forwarder = Forwarder(raw_data)
        forwarder.forward()
        return forwarder.response


class TCPProxyHandler(  # socketserver.ThreadingMixIn,
                      socketserver.BaseRequestHandler):
    chunk_size = 4096

    def __init__(self, *args, **kwargs):
        self.emailer = EmailConnection()
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
        response = self.emailer.forward(data)
        logger.debug("Received response\n%s", response)
        for chunk in response.iter_content(self.chunk_size):
            self.request.sendall(chunk)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(proxy_settings)
    HOST, PORT = "localhost", 9999
    logger.debug("Creating proxy server at {}:{}".format(HOST, PORT))

    # Create the server, binding to localhost on port 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TCPProxyHandler)
    logger.debug("Server created.")

    logger.debug("Placing server into non-blocking mode.")
    tcp_server.socket.setblocking(False)
    logger.debug('Done.')

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    logger.debug("Starting server.")
    try:
        tcp_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tcp_server.shutdown()

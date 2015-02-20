import imaplib2
from io import BytesIO
import asyncore
import logging
from smtpd import SMTPServer
from http.client import parse_headers, email

import requests
import sys
import email_utils

from configure import remote_settings as rs

logger = logging.getLogger(
    'remote' if __name__ == '__main__' else __name__)


class RemoteServerException(Exception):
    pass


class Forwarder:
    def __init__(self, raw_request):
        self.raw = raw_request
        self.connection = self.response = None
        self.close_connection = True

        # Parse the raw request into constituents
        csrf = b'\r\n'
        request_lines = self.raw.split(csrf)
        request = str(request_lines[0], 'iso-8859-1')
        split = request.split()

        if len(split) == 3:
            self.method, self.path, self.version = request.split()
        elif len(split) == 2:
            self.method, self.path = request.split()
        else:
            # TODO: More refined error-checking?
            logging.error('Bad request:\n%s', request)
            raise RemoteServerException('Bad request')
        headers = csrf.join(request_lines[1:])
        self.headers = parse_headers(BytesIO(headers))

    def forward(self):
        """
        Forward request to its destination. Returns a
        requests.Response object
        """
        logger.debug("path = %s", self.path)
        self.response = requests.request(
            method=self.method.lower(),
            url=self.path, headers=self.headers)
        return self.response


def log_message(peer, mail_from, recipient_list, data,
                logging_level=logging.DEBUG):
    """Log the email message.

    :param peer: Peer host from the SMTP server.
    :param mail_from: `From` email address
    :param recipient_list: List of `To` email addresses.
    :param data: Raw message data.
    :param logging_level: Level to log. Default is `logging.DEBUG`.

    :return: None
    """

    # Shortcut return
    if not logger.isEnabledFor(logging_level):
        return

    is_in_headers = True
    lines = data.split('\n')

    msg = '\n'
    msg += 'From: %s' % mail_from
    msg += 'To: %s' % recipient_list
    msg += '---------- MESSAGE ----------'
    for line in lines:
        # headers first
        if is_in_headers and not line:
            is_in_headers = False
            msg += 'X-Peer: %s:%d' % (peer[0], peer[1])
        logger.log(logging_level, line)
    logger.log(logging_level, '------------ END ------------')


class TCPTunnelServer(SMTPServer):

    def process_message(self, peer, mail_from, recipient_list, data):
        message = email_utils.unpack(email.message_from_string(data))
        logger.debug('Received message:\n%s', message.decode())
        logger.debug('Forwarding...')
        try:
            response = Forwarder(message).forward()
        except RemoteServerException:
            logger.error('Caught exception; no response possible.')
            return u'252 Cannot VRFY user, but will accept message and attempt delivery'

        # Great! We've got a response.

        return u'250 OK'


def run(**kwargs):
    """Run the remote server forever

    Key-value parameters are taken to be settings.
    """

    # TODO Use IMAP IDLE connection to wait for email coming in
    # Once the connection is broken, we check for email.
    rs.configure(**kwargs)

    logging.basicConfig(level=rs.LOGGING_LEVEL)
    host = rs.SMTP_SERVER
    port = rs.SMTP_PORT

    logger.debug('Starting server on %s:%d', host, port)
    remote_server = TCPTunnelServer((host, port), None)

    logger.debug('Starting asyncore loop.')
    try:
        asyncore.loop()
    finally:
        logger.debug('Loop finished.')
        remote_server.close()

if __name__ == '__main__':

    print(rs)
    logging.basicConfig(level=rs.LOGGING_LEVEL)
    logging.debug("Connecting to %s:%d", rs.IMAP_SERVER, rs.IMAP_PORT)

    if rs.IMAP_USE_SSL:
        imap = imaplib2.IMAP4_SSL(rs.IMAP_SERVER, rs.IMAP_PORT)
    else:
        imap = imaplib2.IMAP4(rs.IMAP_SERVER, rs.IMAP_PORT)

    logging.debug("Connecting as user %s", rs.IMAP_USER)
    imap.login(rs.IMAP_USER, rs.IMAP_PASSWORD)
    logging.debug("Logged in.")

    logging.debug("Calling IDLE")
    imap.select('Inbox', readonly=True)
    print(imap.uid('search', None, 'SUBJECT', 'test'))
    for i in range(10):
        print('Idle')
        print(imap.idle())
        print('Broke.')

    logging.debug("Done.")

    logging.debug("Closing connection and logging out...")

    sys.exit()

    try:
        run()
    except KeyboardInterrupt:
        pass
    sys.exit()



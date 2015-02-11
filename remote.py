from io import BytesIO
import asyncore
import logging
from smtpd import SMTPServer
from http.client import parse_headers

import requests
import sys
import email_utils

from configure import remote_settings as rs

logger = logging.getLogger(__name__)


class Forwarder:

    def __init__(self, raw_request):
        self.raw = raw_request
        self.connection = self.response = None
        self.close_connection = True

        # Parse the raw request into constituents
        csrf = b'\r\n'
        request_lines = self.raw.split(csrf)
        request = str(request_lines[0], 'iso-8859-1')
        try:
            self.method, self.path, self.version = request.split()
        except ValueError:
            self.method, self.path = request.split()

        headers = csrf.join(request_lines[1:])
        self.headers = parse_headers(BytesIO(headers))

    def forward(self):
        """
        Forward request to its destination. Returns a requests.Response object
        """
        logger.debug("path = %s", self.path)
        self.response = requests.request(method=self.method.lower(),
                                         url=self.path, headers=self.headers)
        return self.response


def log_message(peer, mail_from, recipient_list, data, logging_level=logging.DEBUG):
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
    msg += '---------- MESSAGE FOLLOWS ----------'
    for line in lines:
        # headers first
        if is_in_headers and not line:
            is_in_headers = False
            msg += 'X-Peer: %s:%d' % (peer[0], peer[1])
        logger.log(logging_level, line)
    logger.log(logging_level, '------------ END MESSAGE ------------')


class TCPTunnelServer(SMTPServer):

    def process_message(self, peer, mail_from, recipient_list, data):
        log_message(peer, mail_from, recipient_list, data)
        message = email_utils.unpack(data)
        logger.debug(message)


def run_server(**kwargs):
    """Run the remote server forever

    Key-value parameters are taken to be settings.
    """
    rs.configure(**kwargs)

    logging.basicConfig(level=rs.LOGGING_LEVEL)
    host = rs.SMTP_HOST
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
    sys.exit(run_server())
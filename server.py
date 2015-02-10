from io import BytesIO
import asyncore
import logging
from smtpd import SMTPServer
from http.client import parse_headers

import requests
import email_utils

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
        self.response = requests.request(method=self.method.lower(), url=self.path, headers=self.headers)
        return self.response


def log_message(peer, mail_from, recipient_list, data, logging_level=logging.DEBUG):
    if not logger.isEnabledFor(logging_level):
        return
    is_in_headers = True
    lines = data.split('\n')
    logger.log(logging_level, 'From: %s', mail_from)
    logger.log(logging_level, 'To: %s', recipient_list)
    logger.log(logging_level, '---------- MESSAGE FOLLOWS ----------')
    for line in lines:
        # headers first
        if is_in_headers and not line:
            is_in_headers = False
            logger.debug('X-Peer: %s', peer[0])
        logger.log(logging_level, line)
    logger.log(logging_level, '------------ END MESSAGE ------------')


class TCPTunnelServer(SMTPServer):

    def process_message(self, peer, mail_from, recipient_list, data):
        log_message(peer, mail_from, recipient_list, data)
        message = email_utils.unpack(data)
        logging.debug(message)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    host = 'localhost'
    port = 1111
    logging.debug('Starting server on %s:%d', host, port)
    server = TCPTunnelServer((host, port), None)
    logging.debug('Server statrted.')

    logging.debug('Starting asyncore loop.')
    try:
        asyncore.loop()
    finally:
        logging.debug('Loop finished.')


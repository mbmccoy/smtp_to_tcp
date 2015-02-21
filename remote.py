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


class TCPTunnelServer(SMTPServer):

    def process_message(self, peer, mail_from, recipient_list, data):
        message = email_utils.unpack(email.message_from_string(data))
        logger.debug('Received message:\n%s', message.decode())
        logger.debug('Forwarding...')
        try:
            response = email_utils.Forwarder(message).forward()
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
    logger.setLevel(level=rs.LOGGING_LEVEL)

    smtp_host = rs.SMTP_SERVER
    smtp_port = rs.SMTP_PORT
    imap_host = rs.IMAP_SERVER
    imap_port = rs.IMAP_PORT

    logger.debug('Starting server on %s:%d', smtp_host, smtp_port)
    remote_server = TCPTunnelServer((smtp_host, smtp_port), None)

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



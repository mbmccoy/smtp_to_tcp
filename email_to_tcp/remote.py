from getpass import getpass
import imaplib
import logging
from http.client import HTTPException, LineTooLong
import os
import smtplib
import sys

from requests.exceptions import RequestException

from email_to_tcp import utils


logger = logging.getLogger(
    'remote' if __name__ == '__main__' else __name__)


def run(settings):
    email_connection = utils.EmailConnection(s=settings)

    while True:
        email_candidate = \
            email_connection.fetch(subject=settings.MAIL_PREFIX)
        raw_data = utils.unpack(email_candidate)
        if not raw_data:
            logger.debug("No data unpacked...")
            continue
        try:
            forwarder = utils.Forwarder(raw_data)
            response = forwarder.forward()
        except (ValueError, HTTPException, LineTooLong,
                RequestException, AttributeError) as err:
            logger.debug("Unable to forward email: %s", err)
            continue
        logger.debug("Received response\n%s", response)
        email_connection.reply(response.content, email_candidate)


def configure(s=utils.proxy_settings):
    if not s.SMTP_SERVER:
        s.SMTP_SERVER = input("Enter the SMTP server that the remote server will "
                              "email from (ex: smtp.gmail.com): \n")
    if not s.SMTP_USER:
        s.SMTP_USER = input("SMTP username (ex: example@gmail.com):\n")

    if not s.SMTP_PASSWORD:
        s.SMTP_PASSWORD = getpass("SMTP password: ")

    if not os.environ.get('SMTP_USE_SSL'):
        s.SMTP_USE_SSL = bool(input("Use SSL? [Y/n]").lower() != 'n')
        default_port = s.SMTP_USE_SSL and \
                       smtplib.SMTP_SSL_PORT or smtplib.SMTP_PORT
        s.SMTP_PORT = int(input("Port (default %d): " % default_port)
                          or default_port)

    if not s.IMAP_SERVER:
        s.IMAP_SERVER = input("Enter the IMAP server that the remote server "
                              "will listen to (ex: imap.gmail.com): \n")
    if not s.IMAP_USER:
        s.IMAP_USER = input("The IMAP username (default %s): \n"
                            % s.SMTP_USER) or s.SMTP_USER
    if not s.IMAP_PASSWORD:
        s.IMAP_PASSWORD = getpass("IMAP password: ")

    if not os.environ.get('IMAP_USE_SSL'):
        s.IMAP_USE_SSL = bool(input("Use SSL? [Y/n]").lower() != 'n')
        default_port = s.IMAP_USE_SSL and \
            imaplib.IMAP4_SSL_PORT or imaplib.IMAP4_PORT
        s.IMAP_PORT = int(input("Port (default %d): " % default_port)
                          or default_port)

    return s


if __name__ == '__main__':
    logging.basicConfig(level=utils.settings.LOGGING_LEVEL)

    settings = utils.settings
    settings = configure(settings)
    try:
        run(settings=settings)
    except KeyboardInterrupt:
        sys.exit(0)
    sys.exit(-1)






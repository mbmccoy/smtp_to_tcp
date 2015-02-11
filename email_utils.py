import logging

import smtplib
import imaplib

import email
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


__author__ = '__mccoy__'

logger = logging.getLogger(__name__)


def hash_filename(data):
    """Convert data into a unique filename"""
    key = str(hash(data))
    return key + '.pkt'


def unhash_filename(filename):
    return int(filename.split('.')[0])


def pack(mail_from, recipient_list, data):
    """"Pack TCP request data into an email"""

    # Base message
    package = MIMEMultipart()
    package['Subject'] = 'TEST'
    package['To'] = recipient_list[0]
    package['From'] = mail_from
    package.preamble = 'TEST'

    # Create attachment
    attachment_type = 'application/octet-stream'
    maintype, subtype = attachment_type.split('/', 1)
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(data)

    # Add to base message
    email.encoders.encode_base64(attachment)
    attachment.add_header('Content Disposition', 'attachment', filename=hash_filename(data))
    package.attach(attachment)

    return package


def unpack(message):
    """Unpack the message payload (inverse of pack)"""

    if isinstance(message, str):
        message = email.message_from_string(message)
    elif isinstance(message, bytes):
        message = email.message_from_bytes(message)

    if not isinstance(message, email.message.Message):
        raise TypeError('Argument message must be either str, bytes, or MIME email message, not type {}'.format(
            type(message)))

    payload = None
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        payload = part.get_payload(decode=True)
        logger.debug("Email payload: %s", payload)

    return payload


class EmailConnection:

    def __init__(self, sender, recipients,
                 smtp_host='localhost', smtp_port=1111,
                 imap_host='localhost', imap_port=imaplib.IMAP4_PORT):

        self.sender = sender
        self.recipients = recipients

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_server = smtplib.SMTP(smtp_host, smtp_port)
        self.smtp_server.set_debuglevel(True)  # show communication with the server

        self.imap_host = imap_host
        self.imap_port = imap_port
        self.imap_server = imaplib.IMAP4(imap_host, imap_port)

    def send_email(self, message):
        self.smtp_server.sendmail(self.sender, self.recipients, message)

    def __del__(self):
        self.smtp_server.close()

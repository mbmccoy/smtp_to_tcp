import base64
import logging

import smtplib

import email
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from http.client import parse_headers
from io import BytesIO

import petname

import imaplib2
import requests

from configure import proxy_settings

logger = logging.getLogger(__name__)

MAIL_PREFIX = '[MailTunnel]'


class EmailException(Exception):
    pass


class FormatException(Exception):
    pass


def generate_filename():
    """Convert data into a unique filename"""
    name = petname.Generate(3, '-')
    return name + '.pkt'


def pack(mail_from, recipient_list, subject, data):
    """"Pack TCP request data into an email"""

    # Base message
    package = MIMEMultipart()
    package['Subject'] = subject
    package['To'] = recipient_list[0]
    package['From'] = mail_from

    # Create attachment
    attachment_type = 'application/octet-stream'
    maintype, subtype = attachment_type.split('/', 1)
    attachment = MIMEBase(maintype, subtype)
    attachment.set_payload(data)

    # Add to base message
    email.encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment',
                          filename=generate_filename())
    package.attach(attachment)

    return package


def unpack(message):
    """Unpack the message payload (inverse of pack)"""

    if isinstance(message, str):
        message = email.message_from_string(message)
    elif isinstance(message, bytes):
        message = email.message_from_bytes(message)

    if not isinstance(message, email.message.Message):
        raise TypeError(
            'Argument message must be either str, bytes, or MIME '
            'email message, not type {}'.format(type(message)))

    payload = None
    for part in message.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        filename = part.get_filename()
        if not filename:
            logger.debug("No filename")
            continue
        payload = part.get_payload(decode=True)
        logger.debug("Email payload: %s", payload)
    return payload


def base64_encode(data):
    """Break a bytestring into lines separated by CLRFs, with maximum
    line length specified by `max_length`. Note that `max_length`
    includes length of the carriage return characters."""

    assert (isinstance(data, bytes))
    return str(base64.encodebytes(data), 'ascii')


def base64_decode(encoded):
    """Inverse of `base64_encode`"""
    b_encoded = encoded.encode('ascii', 'surrogateescape')
    s = b''.join(b_encoded.splitlines())
    return base64.b64decode(s, validate=True)


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
            self.method, self.path, self.version = split
        elif len(split) == 2:
            self.method, self.path = split
        else:
            raise ValueError('Bad request: %s' % request)
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


class EmailConnection:
    """Houses both an SMTP and IMAP connection for bidirectional packet
    communication through email. This class takes care of sending and
    receiving the responses from the email server, packaging up the
    data to send, etc.
    """

    def __init__(self, settings):

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

        # TODO: Chekc if IDLE is allowed, and if not, revert to polling

    def send(self, data, subject=None):
        """Forward the data"""

        subject = subject if subject else \
            MAIL_PREFIX + ' ' + petname.Generate(3, ' ')

        package = pack(self.from_email, [self.to_email],
                       subject, data)

        logging.debug("Sending message: %s", package.as_string())
        self.smtp.sendmail(
            self.from_email, [self.to_email], package.as_string())
        return subject

    def reply(self, data, initial_email):
        """Reply to an email with new data.
        :param data:
        :param initial_email:  Message object with the email we are replying to
        :return: the email package that was sent
        """
        subject = 'Re: ' + initial_email['subject']
        to_email = initial_email['from']
        from_email = initial_email['to']

        package = pack(from_email, [to_email], subject, data)
        logging.debug("Replying with message: %s", package.as_string())
        self.smtp.sendmail(from_email, [to_email], package.as_string())
        return package


    def fetch(self, subject=None, email_from=None):
        """Fetch the email response corresponding to a specific request

        Algorithm overview:
         1. Make an IMAP IDLE call.
         2. When the idle breaks or timeouts, check if there is a
         message with whose subject line contains the 'subject'
         argument.
         3. If not, go back to IDLE (step 1).
         4. Otherwise, unpack the data from the message and return.
        """

        if not subject and not email_from:
            raise ValueError("At least one of `subject` or "
                             "`email_from` must be defined.")

        search_args = ["(UNSEEN)"]
        search_args += ["SUBJECT", subject] if subject else []
        search_args += ["FROM", email_from] if email_from else []

        # TODO Timeout implementation
        # TODO Implement something other than IDLE?
        search_results = ['']
        logger.debug('IDLE loop started...')
        while True:
            status, message = self.imap.idle(timeout=90)
            logger.debug("IDLE broken: %s : %s", status, message)
            status, search_results = \
                self.imap.uid('search', None, *search_args)
            logger.debug("Search results %s : %s", status, search_results)
            if search_results[0]:
                break
        unique_ids = search_results[0].split()
        if len(unique_ids) > 1:
            logger.warn("Too many responses from search query SUBJECT %s",
                        subject)

        # Get the most recent message
        status, raw_data = self.imap.uid("fetch", unique_ids[-1], '(RFC822)')
        logger.debug("Response STATUS: %s\nDATA: %s", status, raw_data)
        response_email = email.message_from_string(raw_data[0][1])

        return response_email

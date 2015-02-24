import imaplib
import sys
import unittest
import logging

import smtplib
from configure import proxy_settings as ps

import utils

logger = logging.getLogger(__name__)


class TestEmailUtilities(unittest.TestCase):
    """Tests for encoding and decoding filenames assocated with data"""

    request = b'GET http://www.google.com/favicon.ico HTTP/1.1\r\n' \
              b'Host: www.google.com\r\n' \
              b'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10;' \
              b' rv:34.0) Gecko/20100101 Firefox/34.0\r\n' \
              b'Accept: image/png,image/*;q=0.8,*/*;q=0.5\r\n' \
              b'Accept-Language: en-US,en;q=0.5\r\n' \
              b'Accept-Encoding: gzip, deflate\r\n' \
              b'Cookie: _ga=; JobsSrc=; OGPC=5061451-1:5061416-1:\r\n' \
              b'Connection: keep-alive\r\n\r\n'

    def test_packing(self):
        """Test email message packing/unpacking."""

        payload = utils.pack('mccoy@localhost',
                             ['smtp2tcp@localhost'],
                             'TestSubject',
                             self.request)
        logger.debug(payload)
        unpacked = utils.unpack(payload)
        self.assertEqual(unpacked, self.request)

    def test_linebreaks(self):
        """Test base64_encode
        and base64_decode"""

        self.assertEqual(
            utils.base64_decode(
                utils.base64_encode(
                    self.request)),
            self.request)


class TestProxy(unittest.TestCase):
    """Tests for the proxy servers."""

    def test_smtp_settings(self):
        """Check that the SMTP settings let us log in to the server.

        If you get an error here, you probably need to check the
        environment variables that define the proxy settings.

        """
        if ps.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(ps.SMTP_SERVER,
                                      ps.SMTP_PORT)
        else:
            server = smtplib.SMTP(ps.SMTP_SERVER, ps.SMTP_PORT)
        server.login(ps.SMTP_USER, ps.SMTP_PASSWORD)
        server.close()

    def test_imap_settings(self):
        """Check that the IMAP settings let us log in to the server

        If you get an error here, you probably need to check the
        environment variables that define the remote server settings.
        """
        if ps.IMAP_USE_SSL:
            server = imaplib.IMAP4_SSL(ps.IMAP_SERVER, ps.IMAP_PORT)
        else:
            server = imaplib.IMAP4(ps.IMAP_SERVER, ps.IMAP_PORT)

        server.login(ps.IMAP_USER, ps.IMAP_PASSWORD)
        server.select()
        server.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(unittest.main())
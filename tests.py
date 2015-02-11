import getpass
import imaplib
import sys
import unittest
import logging

import smtplib
import email.utils
from email.mime.text import MIMEText

import email_utils
import proxy


logger = logging.getLogger(__name__)


class TestEmailUtilities(unittest.TestCase):
    """Tests for encoding and decoding filenames assocated with data"""

    def test_hash(self):
        """Check that the filename mangling scheme is consistent."""
        data = object()
        filename = email_utils.hash_filename(data)
        self.assertEquals(filename, email_utils.hash_filename(
            email_utils.unhash_filename(filename)))

    def test_packing(self):
        """Test email message packing/unpacking."""
        data = b'GET http://www.google.com/favicon.ico HTTP/1.1\r\n' \
               b'Host: www.google.com\r\n' \
               b'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:34.0) Gecko/20100101 Firefox/34.0\r\n' \
               b'Accept: image/png,image/*;q=0.8,*/*;q=0.5\r\n' \
               b'Accept-Language: en-US,en;q=0.5\r\n' \
               b'Accept-Encoding: gzip, deflate\r\n' \
               b'Cookie: _ga=; JobsSrc=; OGPC=5061451-1:5061416-1:\r\n' \
               b'Connection: keep-alive\r\n\r\n'

        payload = email_utils.pack('mccoy@localhost', ['smtp2tcp@localhost'], data)
        logger.debug(payload)
        unpacked = email_utils.unpack(payload)
        self.assertEquals(unpacked, data)


class TestSettings(unittest.TestCase):

    def test_smtp_settings(self):
        from configure import proxy_settings as sets

        if sets.SMTP_USE_SSL:
            server = smtplib.SMTP_SSL(sets.SMTP_SERVER,
                                      sets.SMTP_PORT)
        else:
            server = smtplib.SMTP(sets.SMTP_SERVER, sets.SMTP_PORT)

        try:
            server.login(sets.SMTP_USER, sets.SMTP_PASSWORD)
        except smtplib.SMTPConnectError:
            logging.error("Unable to log in to the SMTP server. "
                          "Check your SMTP settings in configure.py")
            raise

    def test_imap_settings(self):
        from configure import server_settings as sets




class TestServer(unittest.TestCase):

    def test_server(self):
        msg = MIMEText('This is the body of the message.')
        msg['To'] = email.utils.formataddr(('Recipient', 'recipient@example.com'))
        msg['From'] = email.utils.formataddr(('Author', 'author@example.com'))
        msg['Subject'] = 'Simple test message'

        logger.debug('logging in')
        smtp_server = smtplib.SMTP('127.0.0.1', 1111)
        smtp_server.set_debuglevel(True)  # show communication with the server
        logger.debug('done')
        try:
            logger.debug('sending')
            smtp_server.sendmail('author@example.com', ['recipient@example.com'], msg.as_string())
            logger.debug('done')
        finally:
            smtp_server.quit()



if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    sys.exit(unittest.main())
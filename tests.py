import imaplib
import os
import sys
import unittest
import logging
import signal

import multiprocessing

import smtplib
import email.utils
from email.mime.text import MIMEText

from configure import proxy_settings as ps, RemoteSettings

import email_utils
import proxy
import remote

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

    def test_hash(self):
        """Check that the filename mangling scheme is consistent."""
        data = object()
        filename = email_utils.hash_filename(data)
        self.assertEqual(filename,
                         email_utils.hash_filename(
                             email_utils.unhash_filename(filename)))

    def test_packing(self):
        """Test email message packing/unpacking."""

        payload = email_utils.pack('mccoy@localhost',
                                   ['smtp2tcp@localhost'],
                                   self.request)
        logger.debug(payload)
        unpacked = email_utils.unpack(payload)
        self.assertEqual(unpacked, self.request)


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


class TestRemote(unittest.TestCase):

    def setUp(self):
        """Set up a local server on another process"""
        self.settings = RemoteSettings(
            SMTP_HOST='localhost', SMTP_PORT=1111)

        remote_smtp_server = multiprocessing.Process(
            target=remote.run, kwargs=self.settings.settings(),)
        remote_smtp_server.daemon = True

        logging.debug("Spinning up remote SMTP server emulator...")
        remote_smtp_server.start()
        remote_smtp_server.join(0.25)  # Pause to spin up
        logging.debug("Done.")
        self.remote_smtp_server = remote_smtp_server

    def tearDown(self):
        """Shut down the remote server"""
        # Shut down the remote server using a keyboard interrupt
        if self.remote_smtp_server.exitcode is None:
            logger.debug("Stopping remote server with SIGINT...")
            os.kill(self.remote_smtp_server.pid, signal.SIGINT)
            self.remote_smtp_server.join(0.5)
        if self.remote_smtp_server.exitcode is None:
            logger.error("Remote server is not responding. "
                         "pid: {}".format(self.remote_smtp_server.pid))
        else:
            logger.debug("Remote server successfully killed "
                         "(ignore the the traceback)")

    def test_server_connection(self):
        # Check that we can send email to the remote server
        payload = email_utils.pack('server@example.com', ['author@localhost.com'],
                               TestEmailUtilities.request)

        logger.debug('logging in')
        smtp_server = smtplib.SMTP(self.settings.SMTP_HOST,
                                   self.settings.SMTP_PORT)
        logger.debug('done')
        try:
            logger.debug('sending')
            smtp_server.sendmail('author@example.com',
                                 ['recipient@example.com'],
                                 payload.as_string())
            logger.debug('done')
        finally:
            smtp_server.quit()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    sys.exit(unittest.main())
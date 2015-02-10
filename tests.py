import sys
import unittest
import logging

import email_utils


class TestEmailServices(unittest.TestCase):
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
        logging.debug(payload)
        unpacked = email_utils.unpack(payload)
        self.assertEquals(unpacked, data)






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    sys.exit(unittest.main())
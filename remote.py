import asyncore
import logging
from smtpd import SMTPServer
from http.client import parse_headers, email


from configure import remote_settings
import utils

logger = logging.getLogger(
    'remote' if __name__ == '__main__' else __name__)



if __name__ == '__main__':
    logger.setLevel(remote_settings.LOGGING_LEVEL)
    email_connection = utils.EmailConnection(settings=remote_settings)

    while True:
        email_candidate = \
            email_connection.fetch(email_from=remote_settings.FROM_EMAIL)

        raw_data = utils.unpack(email_candidate)
        try:
            forwarder = utils.Forwarder(raw_data)
        except ValueError, HTTPException, LineTooLong:
            # TODO STOPPED HERE
            raise
        response = forwarder.forward()

        # TODO: Check that the candidate has a valid package,
        # if so, delete the message (if you want)
        # get the response from the server
        # reply with that message





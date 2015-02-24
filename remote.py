import logging
from http.client import HTTPException, LineTooLong
import requests

from requests.exceptions import RequestException

from configure import remote_settings
import utils

logger = logging.getLogger(
    'remote' if __name__ == '__main__' else __name__)

if __name__ == '__main__':
    logging.basicConfig(level=remote_settings.LOGGING_LEVEL)
    email_connection = utils.EmailConnection(settings=remote_settings)

    while True:
        email_candidate = \
            email_connection.fetch(subject=utils.MAIL_PREFIX)
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

        print(email_candidate['subject'])
        print(response)

        email_connection.reply(response.content, email_candidate)





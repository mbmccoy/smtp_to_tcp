import logging
from http.client import HTTPException, LineTooLong

from requests.exceptions import RequestException
import sys

import utils

logger = logging.getLogger(
    'remote' if __name__ == '__main__' else __name__)


def run(settings):
    email_connection = utils.EmailConnection(settings=settings)

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
        email_connection.reply(response.content, email_candidate)


if __name__ == '__main__':
    logging.basicConfig(level=utils.settings.LOGGING_LEVEL)

    try:
        run(settings=utils.settings)
    except KeyboardInterrupt:
        sys.exit(0)
    sys.exit(-1)






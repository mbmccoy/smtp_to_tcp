import logging
import socketserver
from io import BytesIO

import utils

logger = logging.getLogger(
    'proxy' if __name__ == '__main__' else __name__)


class TCPProxyHandler(socketserver.BaseRequestHandler):
    chunk_size = 4096

    email_connection = utils.EmailConnection(utils.proxy_settings)

    def handle(self):
        logger.debug("%s connected", self.client_address[0])
        data = b''
        while True:
            try:
                data += self.request.recv(self.chunk_size)
            except BlockingIOError:
                break
        logger.debug("%s", data)
        subject = self.email_connection.send(data)

        response = self.email_connection.fetch(subject='Re: ' + subject)
        logger.debug("Received response\n%s", response)
        raw_data = BytesIO(utils.unpack(response))

        while True:
            chunk = raw_data.read(self.chunk_size)
            if not chunk:
                break
            self.request.sendall(chunk)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    HOST, PORT = "localhost", 9999
    logger.debug("Creating proxy server at {}:{}".format(HOST, PORT))

    # Create the server, binding to localhost on port 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TCPProxyHandler)
    logger.debug("Server created.")

    logger.debug("Placing server into non-blocking mode.")
    tcp_server.socket.setblocking(False)
    logger.debug('Done.')

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    logger.debug("Starting server.")
    try:
        tcp_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tcp_server.shutdown()

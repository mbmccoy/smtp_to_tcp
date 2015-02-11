"""
===========
settings.py
===========

Defines the default settings for the server and the proxy. It's best practice to
override the settings using environment variables, not by changing the default settings
given here.

"""
import os
import smtplib
import imaplib

import logging


class ProxySettings:
    """Container for proxy settings"""

    LOGGING_LEVEL = logging.DEBUG

    # SMTP settings
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

    SMTP_USE_SSL = True
    SMTP_PORT = SMTP_USE_SSL and smtplib.SMTP_SSL_PORT or smtplib.SMTP_PORT

    # IMAP settings
    IMAP_SERVER = os.environ.get('IMAP_SERVER', SMTP_SERVER)
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', SMTP_PASSWORD)

    IMAP_USE_SSL = True
    IMAP_PORT = IMAP_USE_SSL and imaplib.IMAP4_SSL_PORT or imaplib.IMAP4_PORT


class ServerSettings:
    """Container for server settings"""

    LOGGING_LEVEL = logging.DEBUG

    SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
    SMTP_PORT = os.environ.get('SMTP_PORT', smtplib.SMTP_PORT)


proxy_settings = ProxySettings()
server_settings = ServerSettings()

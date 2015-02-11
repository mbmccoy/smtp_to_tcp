"""
===========
settings.py
===========

Defines the default settings for the server and the proxy. It's best practice to
override the settings using environment variables, not by changing the default settings
given here.

"""
import getpass
import os
import smtplib
import imaplib

import logging


class BaseSettings:
    """Default settings container"""
    def __init__(self, ):
        self._configured = False

        # Convert class attributes to instance attributes
        for key, val in type(self).__dict__.items():
            if not key.startswith('_'):
                self.__dict__[key] = val

    def configure(self, prompt_for_blank=True, prompt_prefix=None, **kwargs):
        """Fill in blank settings

        :param prompt_for_blank: Prompt to fill in blank settings
        :param prompt_prefix: Restrict prompts to settings that start with this prefix.
        """

        # First, set the key-value pairs:
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Now prompt the user for the empty strings
        for key, value in self.__dict__.items():
            if prompt_prefix and not key.startswith(prompt_prefix):
                continue
            if not value and isinstance(value, str) and prompt_for_blank:
                prompt_string = ' '.join(key.lower().split('_')) + ': '
                # Don't let passwords get echoed:
                if 'pass' in key.lower():
                    setattr(self, key, getpass.getpass(prompt_string))
                else:
                    setattr(self, key, input(prompt_string))

        self._configured = True


class ProxySettings(BaseSettings):
    """Container for proxy settings"""

    # Example settings follow in comments.
    LOGGING_LEVEL = logging.DEBUG

    # SMTP settings

    # Set these to your usual outgoing SMTP settings.
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')  # smtp.gmail.com
    SMTP_USER = os.environ.get('SMTP_USER', '')  # example@gmail.com
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')  # BaDPaSSwOrd

    # You must use SSL for most commercial SMTP servers e.g gmail
    SMTP_USE_SSL = True

    # Use default ports for SSL or unencrypted
    SMTP_PORT = SMTP_USE_SSL and smtplib.SMTP_SSL_PORT or smtplib.SMTP_PORT

    # IMAP settings (inherited from SMTP settings if not defined)
    IMAP_SERVER = os.environ.get('IMAP_SERVER', SMTP_SERVER)
    IMAP_USER = os.environ.get('IMAP_USER', SMTP_USER)
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', SMTP_PASSWORD)

    IMAP_USE_SSL = True
    IMAP_PORT = IMAP_USE_SSL and imaplib.IMAP4_SSL_PORT or imaplib.IMAP4_PORT


class RemoteSettings(BaseSettings):
    """Container for server settings"""

    LOGGING_LEVEL = logging.DEBUG

    SMTP_USE_SSL = False  # TODO: Support SSL for the server?
    SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
    SMTP_PORT = os.environ.get('SMTP_PORT', smtplib.SMTP_PORT)


proxy_settings = ProxySettings()
remote_settings = RemoteSettings()

"""
===========
settings.py
===========

Defines the default settings for the server and the proxy. It's best
practice to override the settings using environment variables, not
by changing the default settings given here.
"""
import getpass
import os
import smtplib
import imaplib

import logging


class BaseSettings:
    """Default settings container"""
    def __init__(self, **kwargs):
        self._configured = False

        # Convert class attributes to instance attributes
        for key, val in type(self).__dict__.items():
            if not key.startswith('_'):
                self.__dict__[key] = val

        if kwargs:
            self.configure(**kwargs)

    def configure(self, prompt_for_blank=True, prompt_prefix=None, **kwargs):
        """Fill in blank settings

        :param prompt_for_blank: Prompt to fill in blank settings
        :param prompt_prefix: Restrict prompts to settings that start
        with this prefix.
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

    def settings(self):
        """Dictionary of all settings defined."""
        return {
            key: val for key, val in self.__dict__.items()
            if not key.startswith('_')
        }

    def __str__(self):
        """Prints all uppercase names that don't have 'PASS' in them"""
        def star_pass(name, value):
            if 'pass' in name.lower():
                return '********'
            else:
                return value
        return '\n'.join(["{} = {}".format(name, star_pass(name, value))
                          for name, value in self.__dict__.items()
                          if name == name.upper()])


class Settings(BaseSettings):
    """Container for proxy settings"""

    # Example settings follow in comments.
    LOGGING_LEVEL = logging.DEBUG

    # SMTP settings
    # Set these to your usual outgoing SMTP settings.
    SMTP_SERVER = os.environ.get('SMTP_SERVER')  # smtp.gmail.com
    SMTP_USER = os.environ.get('SMTP_USER')  # example@gmail.com
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')  # BaDPaSSwOrd

    # You must use SSL for most commercial SMTP servers e.g gmail
    SMTP_USE_SSL = bool(os.environ.get('SMTP_USE_SSL', '1'))
    SMTP_PORT = SMTP_USE_SSL and smtplib.SMTP_SSL_PORT or smtplib.SMTP_PORT

    # IMAP settings
    # Inherit from SMTP settings if not defined
    IMAP_SERVER = os.environ.get('IMAP_SERVER', SMTP_SERVER)
    IMAP_USER = os.environ.get('IMAP_USER', SMTP_USER)
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', '')

    IMAP_USE_SSL = bool(os.environ.get('IMAP_USE_SSL', '1'))
    IMAP_PORT = IMAP_USE_SSL and imaplib.IMAP4_SSL_PORT or imaplib.IMAP4_PORT

    FROM_EMAIL = SMTP_USER
    TO_EMAIL = os.environ.get('TO_EMAIL', SMTP_USER)

RemoteSettings = Settings

proxy_settings = Settings()
remote_settings = RemoteSettings()

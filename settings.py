"""
===========
settings.py
===========

Defines the default settings for the server and the proxy. For the most part, you should
override the settings using environment variables, not by changing the default settings
given here.

-----
Usage
-----
You should import the proxy_settings or the server_settings object from this file (inspired
by Django's method for settings), and not instantiate the class yourself.

   >>> from settings import proxy_settings
   >>> try:
           proxy_settings.SMTP_USE_SSL

"""
import getpass
import os


class BaseSettings:
    """Default settings container"""
    def __init__(self, ):
        self._configured = False
        # Convert class attributes to instance attributes
        for key, val in type(self).__dict__.items():
            if not key.startswith('_'):
                self.__dict__[key] = val

    def prompt_for_blank(self):
        """Prompt to fill in values for missing settings."""
        for key, value in self.__dict__.items():
            if not value and isinstance(value, str):
                prompt_string = ' '.join(key.lower().split('_')) + ': '
                if 'pass' in key.lower():
                    setattr(self, key, getpass.getpass(prompt_string))
                else:
                    setattr(self, key, input(prompt_string))
        self._configured = True


class DefaultProxySettings(BaseSettings):
    """Container for proxy settings"""
    SMTP_USE_SSL = True
    SMTP_SERVER = os.environ.get('SMTP_SERVER', '')
    SMTP_USER = os.environ.get('SMTP_USER', '')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')

    IMAP_SERVER = os.environ.get('IMAP_SERVER', '')
    IMAP_PASSWORD = os.environ.get('IMAP_PASSWORD', '')


class DefaultServerSettings(BaseSettings):
    """Container for server setttings"""
    pass


proxy_settings = DefaultProxySettings()
server_settings = DefaultServerSettings()
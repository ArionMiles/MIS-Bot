"""Mixpanel analytics dashboard object. Used to track events."""
from os import environ
from mixpanel import Mixpanel

mp = Mixpanel(environ.get('MIXPANEL_TOKEN'))

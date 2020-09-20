from urllib.parse import urljoin
from urllib.parse import urlparse

from flask import request


def asbool(obj):
    """
    Interprets an object as a boolean value.
    :rtype: bool
    """

    if isinstance(obj, str):
        obj = obj.strip().lower()
        if obj in ("true", "yes", "on", "y", "t", "1"):
            return True
        if obj in ("false", "no", "off", "n", "f", "0"):
            return False
        raise ValueError('Unable to interpret value "%s" as boolean' % obj)
    return bool(obj)


def is_safe_url(target):
    """Test and see if given redirect URL safe to redirect for login

    ref: https://stackoverflow.com/a/61446498/25077

    :param target: Target URL given by login redirection param
    :return: True if the URL is safe, otherwise False
    """
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

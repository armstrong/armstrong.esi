from Cookie import SimpleCookie
from django import test
from django.core.handlers.base import BaseHandler
from django.core.handlers.wsgi import WSGIRequest
from django.db import close_connection
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class LocalHandler(BaseHandler):
    """
    A HTTP Handler that can be used for fetching local URLs from
    application code.

    Based on django.test.client.ClientHandler, with the CSRF hacks removed.
    """
    def __call__(self, environ):
        from django.conf import settings
        from django.core import signals

        # Set up middleware if needed. We couldn't do this earlier, because
        # settings weren't available.
        if self._request_middleware is None:
            self.load_middleware()

        signals.request_started.send(sender=self.__class__)
        try:
            request = WSGIRequest(environ)
            response = self.get_response(request)

            # Apply response middleware.
            for middleware_method in self._response_middleware:
                response = middleware_method(request, response)
            response = self.apply_response_fixes(request, response)
        finally:
            signals.request_finished.disconnect(close_connection)
            signals.request_finished.send(sender=self.__class__)
            signals.request_finished.connect(close_connection)

        return response


class Client(test.Client):
    """
    A class that can act as a client for fetching local URLs.

    This removes most of the testing behavior from test.Client by using
    LocalHandler, and allows cookies to be specified. The only testing
    behavior that seems to remain is adding the contexts and names of
    rendered templates to the response object, which can be avoided by
    overriding request() if desired.
    """
    def __init__(self, cookies=None, handler_class=LocalHandler, **defaults):
        self.handler = handler_class()
        self.defaults = {'SERVER_NAME': 'localserver'}
        self.defaults.update(defaults)
        self.cookies = SimpleCookie(cookies or {})
        self.exc_info = None
        self.errors = StringIO()

    def store_exc_info(self, **kwargs):
        pass

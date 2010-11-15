class BaseEsiMiddleware(object):
    def process_request(self, request):
        request._esi_was_invoked = False


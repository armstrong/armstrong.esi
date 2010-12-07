from django.http import HttpResponse
from django.utils.cache import cc_delim_re, patch_vary_headers
from django.utils.http import http_date


def hello(request, number=None):
    if request.GET:
        pairs = ('%s = %s' % (key, request.GET[key]) for key in sorted(request.GET))
        return HttpResponse(', '.join(pairs))
    return HttpResponse(number or 'Hello World!')

def cookie_view(request, number):
    response = HttpResponse('C is for cookie.')
    response.set_cookie('a', 'apple')
    response.set_cookie('b', 'banana', path='/cookies/')
    response.set_cookie('number', number)
    return response

def last_modified(request, timestamp):
    response = HttpResponse(timestamp)
    response['Last-Modified'] = http_date(long(timestamp))
    return response

def vary(request):
    response = HttpResponse(request.GET['headers'])
    patch_vary_headers(response, cc_delim_re.split(request.GET['headers']))
    return response

def text(request):
    return HttpResponse('a' * 500)

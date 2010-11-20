from django.http import HttpResponse


def hello(request, number=None):
    if request.GET:
        pairs = ('%s = %s' % (key, request.GET[key]) for key in sorted(request.GET))
        return HttpResponse(', '.join(pairs))
    return HttpResponse(number or 'Hello World!')

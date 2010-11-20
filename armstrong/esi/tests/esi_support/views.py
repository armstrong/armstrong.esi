from django.http import HttpResponse


def hello(request, number=None):
    return HttpResponse(number or '')

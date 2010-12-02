def esi(request):
    if getattr(request, '_esi', None) is None:
        request._esi = {'used': False}
    return {'_esi': request._esi}


def esi(request):
    return {'_esi_was_invoked': request._esi_was_invoked}

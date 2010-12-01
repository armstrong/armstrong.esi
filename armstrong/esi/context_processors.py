
# TODO: Double check that this'll work as expected inside a full example environment
def esi(request):
    return {'_esi_fragment_urls': request._esi_fragment_urls}

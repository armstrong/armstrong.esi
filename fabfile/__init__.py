from ._utils import *

@task
def test():
    settings = {
        'INSTALLED_APPS': (
            'armstrong.esi',
            'armstrong.esi.tests.esi_support',
        ),
        'ROOT_URLCONF': 'armstrong.esi.tests.esi_support.urls',
    }
    run_tests(settings, 'esi_support', 'esi')


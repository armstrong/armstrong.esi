from ._utils import *

@task
def test():
    settings = {
        'INSTALLED_APPS': (
            'armstrong.esi',
            'armstrong.esi.tests.support',
        ),
        'ROOT_URLCONF': 'armstrong.esi.tests.support.urls',
    }
    run_tests(settings, 'esi')


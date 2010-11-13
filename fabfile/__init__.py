from ._utils import *

@task
def test():
    try:
        from d51.django.virtualenv.test_runner import run_tests
    except ImportError:
        import sys
        sys.stderr.write("Please install d51.django.virtualenv.test_runner to run these tests\n")
        sys.exit(-1)

    settings = {
        'INSTALLED_APPS': (
            'armstrong.esi',
            'armstrong.esi.tests.support',
        ),
        'ROOT_URLCONF': 'armstrong.esi.tests.support.urls',
    }
    run_tests(settings, 'esi')


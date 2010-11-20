from ._utils import *

settings = {
    'INSTALLED_APPS': (
        'armstrong.esi',
        'armstrong.esi.tests.esi_support',
    ),
    'TEMPLATE_CONTEXT_PROCESSORS': [
        'armstrong.esi.context_processors.esi',
    ],
    'ROOT_URLCONF': 'armstrong.esi.tests.esi_support.urls',
    'DEBUG_PROPAGATE_EXCEPTIONS': True,
}

@task
def test():
    run_tests(settings, 'esi_support', 'esi')

@task
def shell():
    from d51.django.virtualenv.base import VirtualEnvironment
    v = VirtualEnvironment()
    v.run(settings)
    v.call_command('shell')

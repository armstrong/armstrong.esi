from armstrong.dev.tasks import *

settings = {
    'DEBUG': True,
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


full_name = "armstrong.esi"
main_app = "esi"
tested_apps = ("esi", )
pip_install_first = True

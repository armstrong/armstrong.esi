from setuptools import setup

setup(
    name='armstrong.esi',
    version='0.2',
    description='Base functionality that needs to be shared widely',
    author='Texas Tribune',
    author_email='tech@texastribune.org',
    url='http://github.com/texastribune/armstrong.esi/',
    packages=[
        'armstrong',
        'armstrong.esi',
        'armstrong.esi.templatetags',
    ],

    install_requires=[
        'setuptools',
    ],

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
)

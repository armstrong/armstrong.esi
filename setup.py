"""
setup.py file for building armstrong components.

Nothing in this file should need to be edited, please see accompanying
package.json file if you need to adjust metadata about this package.
"""

from distutils.core import setup
import json
import os

info = json.load(open("./package.json"))


def convert_to_str(d):
    """
    Recursively convert all values in a dictionary to strings

    This is required because setup() does not like unicode in
    the values it is supplied.
    """
    d2 = {}
    for k, v in d.items():
        k = str(k)
        if type(v) in [list, tuple]:
            d2[k] = [str(a) for a in v]
        elif type(v) is dict:
            d2[k] = convert_to_str(v)
        else:
            d2[k] = str(v)
    return d2

info = convert_to_str(info)
NAMESPACE_PACKAGES = []


# TODO: simplify this process
def generate_namespaces(package):
    new_package = ".".join(package.split(".")[0:-1])
    if new_package.count(".") > 0:
        generate_namespaces(new_package)
    NAMESPACE_PACKAGES.append(new_package)
generate_namespaces(info["name"])


if os.path.exists("MANIFEST"):
    os.unlink("MANIFEST")

# Borrowed and modified from django-registration
# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)


def build_package(dirpath, dirnames, filenames):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'):
            del dirnames[i]
    if '__init__.py' in filenames and 'steps.py' not in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)
    elif filenames:
        # Strip off the length of the package name plus the trailing slash
        prefix = dirpath[len(info["name"]) + 1:]
        for f in filenames:
            # Ignore all dot files and any compiled
            if f.startswith(".") or f.endswith(".pyc"):
                continue
            data_files.append(os.path.join(prefix, f))


[build_package(dirpath, dirnames, filenames) for dirpath, dirnames, filenames
        in os.walk(info["name"].replace(".", "/"))]

setup_kwargs = {
    "author": "Bay Citizen & Texas Tribune",
    "author_email": "dev@armstrongcms.org",
    "url": "http://github.com/armstrong/%s/" % info["name"],
    "packages": packages,
    "package_data": {info["name"]: data_files, },
    "namespace_packages": NAMESPACE_PACKAGES,
    "classifiers": [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
}

setup_kwargs.update(info)
setup(**setup_kwargs)

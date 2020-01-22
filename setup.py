"""
A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# To use a consistent encoding
from codecs import open as file_open
from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with file_open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='nsapi',  # pip install nsapi
    description='api wrapper for Dutch Railways (NS)',
    # long_description=open('README.md', 'rt').read(),
    long_description=long_description,

    # version
    # third part for minor release
    # second when api changes
    # first when it becomes stable someday
    version='3.0.2',
    author='Michiel Scholten',
    author_email='michiel@diginaut.net',

    url='https://github.com/aquatix/ns-api/',
    license='MIT',

    # as a practice no need to hard code version unless you know program won't
    # work unless the specific versions are used
    install_requires=['pytz>=2018.5', 'future'],

    # package_dir={'ns_api': ''},
    py_modules=['ns_api'],
    classifiers=[
        "Topic :: Software Development :: Libraries",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        # "Programming Language :: Python :: 2",
        # "Programming Language :: Python :: 2.4",
        # "Programming Language :: Python :: 2.5",
        # "Programming Language :: Python :: 2.6",
        # "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    zip_safe=True,
)

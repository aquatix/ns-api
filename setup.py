from setuptools import setup

setup(
    name = "nsapi", # pip install pocket
    description = "api wrapper for Dutch Railways (NS)",
    #long_description=open('README.md', 'rt').read(),

    # version
    # third part for minor release
    # second when api changes
    # first when it becomes stable someday
    version = "2.3",
    author = 'Michiel Scholten',
    author_email = "michiel@diginaut.net",

    url = 'https://github.com/aquatix/ns-api/',
    license = 'MIT',

    # as a practice no need to hard code version unless you know program wont
    # work unless the specific versions are used
    install_requires = ["requests", ],

    py_modules = ["ns_api"],

    zip_safe = True,
)

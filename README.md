ns_api
======

Query the Dutch railways about your routes, getting info on delays and more. See below for the syntax and example output.

## Installation


Create a new virtual-env and install the necessary packages:

```
mkvirtualenv ns-api

pip install -r requirements.txt
```

Alternatively, follow the installation instructions of [ns-notifications](https://github.com/aquatix/ns-notifications), which makes extensive use of this library.


## Example application

For example, I use the library to push notifications about my route to my phone through [Pushbullet](http://pushbullet.com). Take a look at [pyPushBullet](https://github.com/Azelphur/pyPushBullet); you can install it with [PyPI](https://pypi.python.org/pypi) as `pypushbullet`. The program I use to do this has its own repository: [ns-notifications](https://github.com/aquatix/ns-notifications).

=====
nsapi
=====

Query the Dutch railways about your routes, getting info on delays and
more. See below for the syntax and example output.

|PyPI version| |PyPI downloads| |PyPI license|

Installation
------------

From PyPI
~~~~~~~~~

Assuming you already are inside a virtualenv:

.. code-block:: bash

    pip install nsapi

From Git
~~~~~~~~

Create a new virtualenv (if you are not already in one) and install the
necessary packages:

.. code-block:: bash

    git clone https://github.com/aquatix/ns-api.git
    cd ns-api
    mkvirtualenv ns-api
    pip install -r requirements.txt

As part of ns-notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alternatively, follow the installation instructions of `ns-notifications`_,
which makes extensive use of this library to serve notifications to for
example a smartphone. The requirements of both packages can be installed
in the same ``ns-notifications`` one mentioned in the project;
``ns-api`` will be installed through pip from
`PyPI <https://pypi.python.org/pypi/nsapi>`__.

Example application
-------------------

For example, I use the library to push notifications about my route to
my phone through `Pushbullet <http://pushbullet.com>`__. The program I
use to do this has its own repository: `ns-notifications`_.

NS API key
~~~~~~~~~~

To actually be able to query the `Nederlandse Spoorwegen
API <http://www.ns.nl/api/api>`__, you `need to request a
key <https://www.ns.nl/ews-aanvraagformulier/>`__. Provide a good reason
and you will likely get it mailed to you (it might take some days).

.. |PyPI version| image:: https://img.shields.io/pypi/v/nsapi.svg
   :target: https://pypi.python.org/pypi/nsapi/
.. |PyPI downloads| image:: https://img.shields.io/pypi/dm/nsapi.svg
   :target: https://pypi.python.org/pypi/nsapi/
.. |PyPI license| image:: https://img.shields.io/github/license/aquatix/ns-api.svg
   :target: https://pypi.python.org/pypi/nsapi/
.. _ns-notifications: https://github.com/aquatix/ns-notifications

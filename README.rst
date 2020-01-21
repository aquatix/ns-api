=====
nsapi
=====

Query the Dutch railways about your routes, getting info on delays and
more. See below for the syntax and example output.

|PyPI version| |PyPI downloads| |PyPI license| |Code health|

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

Home Assistant
~~~~~~~~~~~~~~

The very useful `Home Assistant <https://www.home-assistant.io/>`_ home automation software `includes an integration for the ns-api <https://www.home-assistant.io/integrations/nederlandse_spoorwegen/>`_. Be sure to check it out.

Also take a look at nsmaps
~~~~~~~~~~~~~~~~~~~~~~~~~~

Bart Römgens created `a fascinating contour map called nsmaps <https://github.com/bartromgens/nsmaps>`_ based on ns-api. It visualises Dutch railways travel information with OpenLayer 3 contour maps to show how long it takes to get somewhere in the Netherlands by train and bicycle.

Example application
-------------------

For example, I use the library to push notifications about my route to
my phone through `Pushbullet <http://pushbullet.com>`__. The program I
use to do this has its own repository: `ns-notifications`_.

NS API key
~~~~~~~~~~

To actually be able to query the `Nederlandse Spoorwegen
API <https://apiportal.ns.nl/>`_, you `need to subscribe
<https://apiportal.ns.nl/products/NsApp>`_. This immediately
gives you a primary and secundary key you need for access.

.. |PyPI version| image:: https://img.shields.io/pypi/v/nsapi.svg
   :target: https://pypi.python.org/pypi/nsapi/
.. |PyPI downloads| image:: https://img.shields.io/pypi/dm/nsapi.svg
   :target: https://pypi.python.org/pypi/nsapi/
.. |PyPI license| image:: https://img.shields.io/github/license/aquatix/ns-api.svg
   :target: https://pypi.python.org/pypi/nsapi/
.. |Code health| image:: https://api.codacy.com/project/badge/Grade/84e8b4b9005b455c8977bb1d8dda2b64
   :target: https://www.codacy.com/manual/aquatix/ns-api?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=aquatix/ns-api&amp;utm_campaign=Badge_Grade
   :alt: Code Health
.. _ns-notifications: https://github.com/aquatix/ns-notifications

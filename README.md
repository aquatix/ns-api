ns_api
======

Query the Dutch railways about your routes, getting info on delays and more. See below for the syntax and example output.

## Installation


Create a new virtual-env and install the necessary packages:

```
mkvirtualenv ns-api
pip install -r requirements.txt
```

Alternatively, follow the installation instructions of [ns-notifications](https://github.com/aquatix/ns-notifications), which makes extensive use of this library to serve notifications to for example a smartphone. The requirements of both packages can be installed in the same `ns-notifications` one mentioned in the project.


## Example application

For example, I use the library to push notifications about my route to my phone through [Pushbullet](http://pushbullet.com). The program I use to do this has its own repository: [ns-notifications](https://github.com/aquatix/ns-notifications).


### NS API key

To actually be able to query the [Nederlandse Spoorwegen API](http://www.ns.nl/api/api), you [need to request a key](https://www.ns.nl/ews-aanvraagformulier/). Provide a good reason and you will likely get it mailed to you (it might take some days).

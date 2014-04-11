import logging
import pylibmc
from flask import Flask
from flask import jsonify
from flask import request
app = Flask(__name__)

# create logger
logger = logging.getLogger('nsapi_server')
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler('nsapi_server.log')
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.ERROR)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# Connect to the Memcache daemon
mc = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})

@app.route('/')
def nsapi_status():
    result = []
    if 'nsapi_run' in mc:
        result.append("nsapi_run: %s" % mc['nsapi_run'])
    result.append("\n".join(mc['nsapi_delays']))
    return "\n".join(result)

@app.route('/disable/<location>')
def disable_notifier(location=None):
    location_prefix = '[location: %s]' % location
    if 'nsapi_run' in mc:
        logger.info('%s nsapi_run was %s, disabling' % (location_prefix, mc['nsapi_run']))
    else:
        logger.info('%s no nsapi_run tuple in memcache, creating with value False' % location_prefix)
    mc['nsapi_run'] = False
    return 'Disabling notifications'

@app.route('/enable/<location>')
def enable_notifier(location=None):
    location_prefix = '[location: %s]' % location
    if 'nsapi_run' in mc:
        logger.info('%s nsapi_run was %s, enabling' % (location_prefix, mc['nsapi_run']))
    else:
        logger.info('%s no nsapi_run tuple in memcache, creating with value True' % location_prefix)
    mc['nsapi_run'] = True
    return 'Enabling notifications'

if __name__ == '__main__':
    # Run on public interface (!) on non-80 port
    #app.debug = True
    app.run(host='0.0.0.0', port=8086)

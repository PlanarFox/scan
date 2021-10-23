import socket
from urllib.parse import urlparse
import requests
from flask import Response
import subprocess
import hashlib

def api_local_host():
    return 'localhost'

def api_root():
    return '/myplatform'

def __host_per_rfc_2732(host):
    "Format a host name or IP for a URL according to RFC 2732"

    try:
        socket.inet_pton(socket.AF_INET6, host)
        return "[%s]" % (host)
    except socket.error:
        return host  # Not an IPv6 address

def api_host_port(hostport):
    """Return the host and port parts of a host/port pair"""
    if hostport is None:
        return (None, None)
    formatted_host = __host_per_rfc_2732(hostport)
    # The "bogus" is to make it look like a real, parseable URL.
    parsed = urlparse("bogus://%s" % (formatted_host))        
    return (None if parsed.hostname == "none" else parsed.hostname,
            parsed.port)

def api_url(host = None,
            path = None,
            port = None,
            protocol = None
            ):

    host = api_local_host() if host is None else str(host)
    # Force the host into something valid for DNS
    # See http://stackoverflow.com/a/25103444/180674
    try:
        host = host.encode('idna').decode("ascii")
    except UnicodeError:
        raise ValueError("Invalid host '%s'" % (host))
    host = __host_per_rfc_2732(host)

    if path is not None and path.startswith('/'):
        path = path[1:]

    if protocol is None:
        protocol = 'http'

    return protocol + '://' \
        + host \
        + ('' if port is None else (':' + str(port))) \
        + api_root() \
        + ('' if path is None else '/' + str(path))

def api_url_hostport(hostport=None,
            path=None,
            protocol=None
            ):
    (host, port) = api_host_port(hostport)
    return api_url(host=host, port=port, path=path, protocol=protocol)

def api_has_platform(hostport, timeout=5):

    r = requests.get(url = api_url_hostport(hostport),
                    timeout=timeout)

    return r.status_code == 200

def json_return(data):
    return Response(data + '\n', mimetype='application/json')

def bad_request(message='Bad Request'):
    return Response(message + '\n', status=400, mimetype='text/plain')
    
def ok(message="OK", mimetype=None):
    return Response(message + '\n', status=200, mimetype=mimetype)

def getv6addr():
    # Catch the Exception outside the function to use logger
    t1 = subprocess.run('ifconfig', shell=True, stdout=subprocess.PIPE, encoding='utf-8')
    result = t1.stdout.split('\n')
    result = list(map(str.strip, result))
    ip = []
    for item in result:
        if item[:5] == 'inet6' and ('global' in item or 'Global' in item):
            ip.append(item.split()[1])
    if len(ip) == 0:
        return False, 'Host don\'t have ipv6 address.'
    return True, ip

def gen_md5(path):
    with open(path, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            chunk = f.read(2024)
            if not chunk:
                break
            md5.update(chunk)
        return md5.hexdigest()

def integrity_check(path, target_md5):
    md5 = gen_md5(path)
    if md5 == target_md5:
        return True  
    return False

def error_record(message, logger, handler, io):
    handler.flush()
    io.read()
    io.seek(0)
    logger.error(message, exc_info=True)
    handler.flush()
    io.seek(0)
    return io.read()
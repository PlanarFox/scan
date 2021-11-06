import socket
from urllib.parse import urlparse
import requests
from flask import Response
import hashlib
import os

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

def file_integrater(file_dict, config, chunk_size = 1048576):
    # Only for plain text files
    # The key is the file name on local machine, the value is the file name on remote machine
    with open('tmp_config', 'w') as f:
        f.write(config)
    with open('integrated', 'w') as f:
        with open('tmp_config', 'r') as fp:
            f.write(str(os.path.getsize('tmp_config')) + '\n')
            f.write(fp.read())
        for local_name, remote_name in file_dict.items():
            f.write(remote_name + '\n')
            f.write(str(os.path.getsize(local_name)) + '\n')
            with open(local_name, 'r') as fp:
                while True:
                    chunk = fp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
    os.remove('tmp_config')
    return os.path.join(os.getcwd(), 'integrated'), hashlib.md5(config.encode()).hexdigest()

def file_saver(request, cwd, chunk_size=1048576):
    tmp_dir = os.path.join(cwd, 'tmp')
    with open(tmp_dir, 'wb') as f:
        while True:
            chunk = request.stream.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
    with open(tmp_dir, 'r') as f:
        while True:
            filename = f.readline().strip()
            if not filename:
                break
            size = int(f.readline().strip())
            with open(os.path.join(cwd, filename), 'w') as fp:
                while size > 0:
                    if size < chunk_size:
                        fp.write(f.read(size))
                        size = 0
                        break
                    else:
                        fp.write(f.read(chunk_size))
                        size -= chunk_size
    os.remove(tmp_dir)
import os
import socket
from urllib.parse import urlparse
import requests
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

def gen_md5(path):
    with open(path, 'rb') as f:
        md5 = hashlib.md5()
        while True:
            chunk = f.read(2024)
            if not chunk:
                break
            md5.update(chunk)
        return md5.hexdigest()

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
 
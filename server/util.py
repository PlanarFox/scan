import socket
from urllib.parse import urlparse
import requests
from flask import Response
import hashlib
import os
import random
import base64
import json
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pkcs1_v1_5
from Crypto.PublicKey import RSA
from task_creation import PARENT_UUID_FILE
from pathlib import Path


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
    return Response(data, mimetype='application/json')

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

def file_integrater(file_dict, cwd, config, chunk_size = 1048576):
    # Only for plain text files
    # The key is the file name on local machine, the value is the file name on remote machine
    rand_num = str(random.randint(0, 1000))
    tmp_config = os.path.join(cwd, f'tmp_config{rand_num}')
    integrated = os.path.join(cwd, f'integrated{rand_num}')
    with open(tmp_config, 'w') as f:
        f.write(config)
    with open(integrated, 'w') as f:
        with open(tmp_config, 'r') as fp:
            f.write(str(os.path.getsize(tmp_config)) + '\n')
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
    os.remove(tmp_config)
    return integrated, hashlib.md5(config.encode()).hexdigest()

def file_saver(request, cwd, chunk_size=1048576):
    rand_num = str(random.randint(0, 1000))
    tmp_dir = os.path.join(cwd, f'tmp{rand_num}')
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

class Rsa_Crypto():  
    def __init__(self, rsa_public_key = None, rsa_private_key = None):
        if rsa_private_key is None:
            self.rsa_private_key = """-----BEGIN RSA PRIVATE KEY-----
        MIICXQIBAAKBgQC+UHO/FX+mqq68COGYqk82/3xw7vfhNJIM58lrjI0T+zXIx6As
        aNgrelM7Z+raDIRDJvdObz6qVbJ5L1IhcreeZWUmEtmOetqtkF4i/rhthVFmSDAK
        yZi8a6/SulpU8bHEsi2M3gyp25pi7R68GzcAmm1yKCusOaABFa4M7vuC8wIDAQAB
        AoGAd7YTmLblPOlQUGclwOogOfArTr6Cnd57oDKMuGIIu/DgvBMV5dltYKvpfwy2
        5cHJ0JPKLEQ9nteZFDF38CJA7QNfmQzZ810w/SNdP7vnhn4aFeY9/MOlZpftfMHJ
        TAAUqrOpVPTiMf5h14vAAu0idCHZJxCgSozpnJH4Kw9D9QECQQDtVv2D7GIUgtRh
        EKOM8r2YaBt89Hfb33QsyAIp+25zHDRkYcIM2lns3UgwlpmBF0ir5tZeKu9NZeKL
        13QxQIsDAkEAzUb280LR8C11ANZYr+BmagBeUOWb9c7hBxb7Pk/Pu4mGHhQSkN3Q
        WeyDB4BX+dLOaPQllvxYr7DxtHvZoGAtUQJBAJNV6VM4LzrkbMtE9QLOvfwaxNWx
        Pab09L3H++/r8gjrfWrDdR9dfW2ZgPMIyopk1exBBNq4dI3rrdN6ENtyYdkCQAvI
        kRBxu39f/KFprHmcFgTrtH5MT+GSWJSBmzZ+elw3jr1XRaGPOhCPZQ4fLe2nTjX0
        HdxG7AhZzeYgXeO44aECQQCJR8rj6X/rZQyGTHU5NPZdnC+SQB9adV8oRzy9dd4w
        P5/8M9YDDwY4JXv7sb8fH7njNpjk7DHXe9RaSED57HV6
        -----END RSA PRIVATE KEY-----
        """
        else:
            self.rsa_private_key = rsa_private_key

        if rsa_public_key is None:
            self.rsa_public_key = """-----BEGIN PUBLIC KEY-----
        MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+UHO/FX+mqq68COGYqk82/3xw
        7vfhNJIM58lrjI0T+zXIx6AsaNgrelM7Z+raDIRDJvdObz6qVbJ5L1IhcreeZWUm
        EtmOetqtkF4i/rhthVFmSDAKyZi8a6/SulpU8bHEsi2M3gyp25pi7R68GzcAmm1y
        KCusOaABFa4M7vuC8wIDAQAB
        -----END PUBLIC KEY-----
        """
        else:
            self.rsa_public_key = rsa_public_key


    def encrypt(self, content):
        """
        进行rsa加密

        :param str content: 待加密字符串
        :return: str result: 加密后的字符串
        """
        content = content.encode('utf-8')
        length = len(content)
        default_length = 117
        # 公钥加密
        pubobj = Cipher_pkcs1_v1_5.new(RSA.importKey(self.rsa_public_key))
        # 长度不用分段
        if length < default_length:
            return base64.b64encode(pubobj.encrypt(content)).decode('utf-8')
        # 需要分段
        offset = 0
        res = []
        while length - offset > 0:
            if length - offset > default_length:
                res.append(pubobj.encrypt(content[offset:offset + default_length]))
            else:
                res.append(pubobj.encrypt(content[offset:]))
            offset += default_length
        byte_data = b''.join(res)
        result = base64.b64encode(byte_data).decode('utf-8')
        return result

    def decrypt(self, content):
        
        """
        进行rsa解密

        :param str content: 待解密字符串
        :return: str result: 解密后的字符串
        """
        
        content = base64.b64decode(content)
        length = len(content)
        default_length = 128
        # 私钥解密
        priobj = Cipher_pkcs1_v1_5.new(RSA.importKey(self.rsa_private_key))
        # 长度不用分段
        if length < default_length:
            return b''.join(priobj.decrypt(content, b'xyz')).decode('utf8')
        # 需要分段
        offset = 0
        res = []
        while length - offset > 0:
            if length - offset > default_length:
                res.append(priobj.decrypt(content[offset:offset + default_length], b'xyz'))
            else:
                res.append(priobj.decrypt(content[offset:], b'xyz'))
            offset += default_length
        result = b''.join(res).decode('utf8')
        return result

def get_parent_task_dir(cwd, uuid) -> tuple[str, str]:
    if (Path(cwd) / PARENT_UUID_FILE).exists():
        with open(Path(cwd) / PARENT_UUID_FILE, 'r') as f:
            uuid = f.read().strip()
        cwd = Path(cwd).resolve().parent / uuid
    return cwd, uuid
#!/bin/sh
/usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
/usr/sbin/nginx
/bin/bash
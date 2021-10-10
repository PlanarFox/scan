#!/bin/sh
/usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini
/usr/sbin/nginx
/bin/bash
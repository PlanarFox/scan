#!/bin/sh
/usr/local/bin/uwsgi --stop /var/lib/scan/server/uwsgi.pid
/usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini
cp -f /var/lib/scan/server/nginx-flask.conf /etc/nginx/conf.d/server.conf
/usr/sbin/nginx -s stop
/usr/sbin/nginx
/bin/bash
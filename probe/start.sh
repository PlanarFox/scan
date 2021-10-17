#!/bin/sh
/usr/local/bin/uwsgi --stop /var/lib/scan/probe/uwsgi.pid
/usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf
/usr/sbin/nginx -s stop
/usr/sbin/nginx
/bin/bash
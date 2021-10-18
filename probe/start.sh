#!/bin/sh
/usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf
/usr/sbin/nginx
nohup /usr/local/bin/python /var/lib/scan/probe/daemon.py $1 &
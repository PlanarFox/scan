#!/bin/sh
/usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini
cp -f /var/lib/scan/server/nginx-flask.conf /etc/nginx/conf.d/server.conf
/usr/sbin/nginx
nohup /usr/local/bin/python /var/lib/scan/server/daemon.py $1 &
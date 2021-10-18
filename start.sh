#!/bin/sh
/usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
/usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini
cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf
cp -f /var/lib/scan/server/nginx-flask.conf /etc/nginx/conf.d/server.conf
/usr/sbin/nginx
nohup /usr/local/bin/python /var/lib/scan/probe/daemon.py $1 &
nohup /usr/local/bin/python /var/lib/scan/server/daemon.py $2 &
#!/bin/sh
ps -eaf | grep "/usr/local/bin/python /var/lib/scan/probe/daemon.py" | grep -v grep | awk '{ print $2 }' | xargs kill
/usr/local/bin/uwsgi --stop /var/lib/scan/probe/uwsgi.pid
/usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf
/usr/sbin/nginx -s stop
/usr/sbin/nginx
nohup /usr/local/bin/python /var/lib/scan/probe/daemon.py $1 &
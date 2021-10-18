#!/bin/sh
ps -eaf | grep "/usr/local/bin/python /var/lib/scan/server/daemon.py" | grep -v grep | awk '{ print $2 }' | xargs kill
/usr/local/bin/uwsgi --stop /var/lib/scan/server/uwsgi.pid
/usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini
cp -f /var/lib/scan/server/nginx-flask.conf /etc/nginx/conf.d/server.conf
/usr/sbin/nginx -s stop
/usr/sbin/nginx
nohup /usr/local/bin/python /var/lib/scan/server/daemon.py $1 &
#!/bin/sh
ps -eaf | grep "/usr/local/bin/python /var/lib/scan/server/daemon.py" | grep -v grep | awk '{ print $2 }' | xargs kill
/usr/local/bin/uwsgi --stop /var/lib/scan/server/uwsgi.pid
/usr/sbin/nginx -s stop
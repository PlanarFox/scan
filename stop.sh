#!/bin/sh
ps -eaf | grep "/usr/local/bin/python /var/lib/scan/probe/daemon.py" | grep -v grep | awk '{ print $2 }' | xargs kill
ps -eaf | grep "/usr/local/bin/python /var/lib/scan/server/daemon.py" | grep -v grep | awk '{ print $2 }' | xargs kill
/usr/local/bin/uwsgi --stop /var/lib/scan/probe/uwsgi.pid
/usr/local/bin/uwsgi --stop /var/lib/scan/server/uwsgi.pid
/usr/sbin/nginx -s stop
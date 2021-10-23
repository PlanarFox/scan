#!/bin/sh
if [ $# -gt 0 ]
then
    ps -eaf | grep "/usr/local/bin/python /var/lib/scan/probe/daemon.py" | grep -v grep | awk '{ print $2 }' | xargs kill
    /usr/local/bin/uwsgi --stop /var/lib/scan/probe/uwsgi.pid
    if ! test -d /var/lib/scan/probe/log
    then
        mkdir /var/lib/scan/probe/log
    fi
    /usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
    cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf
    /usr/sbin/nginx -s stop
    /usr/sbin/nginx
    nohup /usr/local/bin/python /var/lib/scan/probe/daemon.py $1 > /dev/null &
else
    echo "Please define the probe port. \nRun the command like:./start.sh 8888"
fi
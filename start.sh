#!/bin/sh
if [ $# -gt 1 ]
then
    if ! test -d /var/lib/scan/server/log
    then
        mkdir /var/lib/scan/server/log
    fi
    if ! test -d /var/lib/scan/probe/log
    then
        mkdir /var/lib/scan/probe/log
    fi
    chmod +x /var/lib/scan/server/sort.sh
    /usr/local/bin/uwsgi /var/lib/scan/probe/uwsgi.ini
    /usr/local/bin/uwsgi /var/lib/scan/server/uwsgi.ini
    cp -f /var/lib/scan/probe/nginx-flask.conf /etc/nginx/conf.d/probe.conf
    cp -f /var/lib/scan/server/nginx-flask.conf /etc/nginx/conf.d/server.conf
    /usr/sbin/nginx
    nohup /usr/local/bin/python /var/lib/scan/probe/daemon.py $1 > /dev/null &
    nohup /usr/local/bin/python /var/lib/scan/server/daemon.py $2 > /dev/null &
else
    echo "Please define the probe and server port. \nRun the command like:./start.sh 8888 80\nwhile 80 is for server and 8888 is for probe"
fi
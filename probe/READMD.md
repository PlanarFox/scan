Docker doesn't support ipv6 by default.
We need to set the network mode to host mode.
Run command like "docker -d --network host ..."

You can only have one network interface that connected to the internet
or zmap won't return right result.

PLEASE MANUALLY CHANGE YOUR SERVICE PORT IN FILE nginx-flask.conf AND start.sh
If you want to manully restart the service, port number in restart.sh also need to be changed.
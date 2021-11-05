Docker doesn't support ipv6 by default.
We need to set the network mode to host mode.
Run command like "docker -d --network host ..."

You can only have one network interface that connected to the internet
or zmap won't return right result.

When assigning IPV6 address,  a pair of bracket ([]) is a MUST.

PLEASE MANUALLY CHANGE YOUR SERVICE PORT IN FILE nginx-flask.conf AND start.sh
If you want to manully restart the service, port number in restart.sh also need to be changed.

# zmap
You can assign zmap arguments in the field "[args][args]" of config.yaml.
Use the option itself as the key and specify the value in string form.
The field "--ipv6-source-ip", "--ipv6-target-file" and '-o' will be ignored.
If you want to use ipv4 instead of ipv6
(Need to be completed)
PLEASE END THE TARGET FILE WITH '\n'.
Docker doesn't support ipv6 by default.
We need to set the network mode to host mode.
Run command like "docker -itd --network host ..."

You can only have one network interface that connected to the internet
or zmap won't return right result.
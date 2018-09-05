# Overview

This charm provides [WireGuard][wireguard]. WireGuard describes itself as an
extremely simple yet fast and modern VPN that utilizes state-of-the-art
cryptography. It aims to be faster, simpler, leaner, and more useful than IPSec,
while avoiding the massive headache. It intends to be considerably more
performant than OpenVPN. WireGuard is designed as a general purpose VPN for
running on embedded interfaces and super computers alike, fit for many different
circumstances. Initially released for the Linux kernel, it is now cross-platform
and widely deployable. It is currently under heavy development, but already it
might be regarded as the most secure, easiest to use, and simplest VPN solution
in the industry. 

# Usage

This charm is in initial development and is not feature complete.

To deploy:

    juju deploy cs:~chris.sanders/wireguard

By default the charm sets up as a server, enabling routing of traffic. The
device for the routing traffic defaults to eth0 and can be set with the
configuration option 'forward-dev'. 

The private address is set with the configuration option 'address' and must be
unique. If two servers are deployed as peers one must have the address changed.

Peers are configured with the configuration option 'peers' and expects a base64
encoded string of a yaml configuration. To supply this in a bundle use the
include-base64:// parameter to include the yaml file. To supply this via command
line for a peers.yaml in the current directory:
    juju config wireguard peers="$(base64 ./peers.yaml)"

## Known Limitations and Issues

This charm is under development, several other use cases/features are still under
consideration. Merge requests are appreciated, some examples of current limitations include.

 * No wireguard relation for automatic configuration of two peers
 * Routing is either on or off, no option to limit or blacklist routes on the
   server
 * Functional testing is minimal

# Contact Information

## Upstream Project Information

  - Code: https://github.com/chris-sanders/layer-wireguard 
  - Bug tracking: https://github.com/chris-sanders/layer-wireguard/issues
  - Contact information: sanders.chris@gmail.com

[wireguard]: https://www.wireguard.com/


"""Main reactive layer for the WireGuard charm."""
from charms.reactive import when, when_not, set_flag, endpoint_from_name
from charmhelpers import fetch
from charmhelpers.core import hookenv

from libwireguard import WireguardHelper

import socket

wh = WireguardHelper()


@when_not('wireguard.installed')
def install_wireguard():
    """Perform initial install."""
    hookenv.status_set('maintenance', 'Installing Wireguard')
    fetch.add_source(wh.ppa)
    fetch.apt_update()
    fetch.install('wireguard')
    set_flag('wireguard.installed')


@when('wireguard.installed', 'config.changed')
def configure_wireguard():
    """Configure WireGuard when configuration changes."""
    hookenv.status_set('maintenance', 'Configuring WireGuard')
    wh.configure()
    hookenv.status_set('active', 'WireGuard configured')


@when('reverseproxy.ready')
@when_not('reverseproxy.configured')
def configure_reverseproxy():
    """Configure reverseproxy relation."""
    interface = endpoint_from_name('reverseproxy')
    if wh.charm_config['proxy-via-hostname']:
        internal_host = socket.getfqdn()
    else:
        internal_host = hookenv.unit_public_ip()
    config = {
        'mode': 'tcp',
        'external_port': wh.charm_config['listen-port'],
        'internal_host': internal_host,
        'internal_port': wh.charm_config['listen-port'],
    }
    interface.configure(config)

from charms.reactive import when, when_not, set_flag
from charmhelpers import fetch
from charmhelpers.core import hookenv, host

from libwireguard import WireguardHelper

wh = WireguardHelper()


@when_not('wireguard.installed')
def install_wireguard():
    hookenv.status_set('maintenance', 'Installing Wireguard')
    fetch.add_source(wh.ppa)
    fetch.apt_update()
    fetch.install('wireguard')
    wh.gen_keys()
    set_flag('wireguard.installed')


@when_not('wireguard.configured')
def configure_wireguard():
    hookenv.status_set('maintenance', 'Generating config')
    wh.write_config()
    host.service('enable', wh.service_name)
    host.service('start', wh.service_name)
    hookenv.open_port(wh.charm_config['listen-port'], protocol='UDP')
    hookenv.status_set('active', '')
    set_flag('wireguard.configured')


@when('config.changed')
def update_config():
    host.service('stop', wh.service_name)
    wh.write_config()
    host.service('start', wh.service_name)
    if wh.charm_config.changed('listen-port') and\
       wh.charm_config.previous('listen-port') is not None:
        hookenv.close_port(wh.charm_config.previous('listen-port'), protocol='UDP')
        hookenv.open_port(wh.charm_config['listen-port'], protocol='UDP')

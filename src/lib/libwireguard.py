# import os
import base64
import fileinput
import subprocess
import yaml

from charmhelpers.core import hookenv, templating
from charmhelpers.core.hookenv import log


class WireguardHelper():
    def __init__(self):
        self.charm_config = hookenv.config()
        self.ppa = "ppa:wireguard/wireguard"
        self.key_dir = "/etc/wireguard"
        self.cfg_dir = "/etc/wireguard"
        self.cfg_file = self.cfg_dir + '/wg0.conf'
        self.private_key_file = self.key_dir + '/privatekey'
        self.public_key_file = self.key_dir + '/publickey'
        self.service_name = 'wg-quick@wg0'
        self.sysctl_file = '/etc/sysctl.d/99-sysctl.conf'

    def gen_keys(self):
        cmd = 'wg genkey | tee privatekey | wg pubkey > publickey'
        try:
            subprocess.check_call(cmd, cwd=self.cfg_dir, shell=True)
        except subprocess.CalledProcessError as e:
            log("Failed to modify generate keys", level='error')
            log("Cmd: {}".format(cmd), level='error')
            log("Error: {}".format(e.output), level='error')

    def write_config(self):
        with open(self.private_key_file, 'r') as key:
            private_key = key.read().strip('\n')
        peers_string = base64.b64decode(self.charm_config['peers'])
        peers_yaml = yaml.safe_load(peers_string)
        context = {'private_key': private_key,
                   'listen_port': self.charm_config['listen-port'],
                   'peers': peers_yaml,
                   'address': self.charm_config['address'],
                   'forward': self.charm_config['forward-ip'],
                   'forward_dev': self.charm_config['forward-dev'],
                   }
        templating.render('wg0.conf.j2', self.cfg_file, context, perms=0o660)

    def enable_forward(self):
        cmds = [["sysctl", 'net.ipv4.ip_forward=1'],
                ["sysctl", 'net.ipv6.conf.all.forwarding=1']
                ]
        for cmd in cmds:
            try:
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                log("Failed to enable forwarding:", level='error')
                log("Cmd: {}".format(cmd), level='error')
                log("Error: {}".format(e.output), level='error')
                break
        else:
            with fileinput.input(self.sysctl_file, inplace=True) as f:
                for line in f:
                    if "net.ipv4.ip_forward" in line or\
                       "net.ipv6.conf.all.forwarding" in line:
                        print(line.lstrip('#'), end='')
                    else:
                        print(line, end='')

    def disable_forward(self):
        cmds = [["sysctl", 'net.ipv4.ip_forward=0'],
                ["sysctl", 'net.ipv6.conf.all.forwarding=0']
                ]
        for cmd in cmds:
            try:
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                log("Failed to disable forwarding:", level='error')
                log("Cmd: {}".format(cmd), level='error')
                log("Error: {}".format(e.output), level='error')
                break
        else:
            for line in fileinput.input(self.sysctl_file, inplace=True):
                if "net.ipv4.ip_forward" in line or\
                   "net.ipv6.conf.all.forwarding" in line:
                    print('#' + line, end='')
                else:
                    print(line, end='')

    def get_settings(self):
        with open(self.public_key_file, 'r') as key:
            public_key = key.read().strip('\n')
        port = self.charm_config['listen-port'],
        ip = hookenv.unit_public_ip()
        return public_key, ip, port

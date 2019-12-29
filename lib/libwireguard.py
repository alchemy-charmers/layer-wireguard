"""Helper library for configuring WireGuard."""
import base64
import os
from subprocess import Popen, PIPE, check_call, CalledProcessError
import yaml

from charmhelpers.core import hookenv, templating, host, unitdata
from charmhelpers.core.hookenv import log


class WireguardHelper:
    """Helper class for WireGuard."""

    def __init__(self):
        """Instantiate variables."""
        self.charm_config = hookenv.config()
        self.kv = unitdata.kv()
        self.ppa = "ppa:wireguard/wireguard"
        self.key_dir = "/etc/wireguard"
        self.cfg_dir = "/etc/wireguard"
        self.private_key_file = "{}/privatekey".format(self.key_dir)
        self.public_key_file = "{}/publickey".format(self.key_dir)
        self.cfg_file = self.cfg_dir + "/wg0.conf"
        self.service_name = "wg-quick@wg0"
        self.sysctl_file = "/etc/sysctl.d/99-wireguard-forward.conf"

    def read_file(self, filename):
        """Read the contents of a file (key file) and return the contents without newlines."""
        file_handle = open(filename, "r")
        content = file_handle.read()
        file_handle.close()
        return content.rstrip()

    def migrate_keys(self):
        """Retrieve previously stored keys in flat files, migrate them if they exist."""
        log("Migrating keys to key-value store", level="info")
        if os.path.isfile(self.public_key_file):
            public_key_contents = self.read_file(self.public_key_file)
            self.kv.set("public-key", public_key_contents)
            os.remove(self.public_key_file)
        if os.path.isfile(self.private_key_file):
            private_key_contents = self.read_file(self.private_key_file)
            self.kv.set("private-key", private_key_contents)
            os.remove(self.private_eky_file)
        log("Successfully migrated keys to key-value store", level="info")
        return True

    def run_wg(self, args, stdin=b""):
        """Run wg with the supplied stdin and command, and return stdout."""
        cmd = ["wg"]
        if args:
            cmd.extend(args)
        process = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate(stdin)
        hookenv.log(
            "Run wg command {}.\nstdout: {}\nstderr: {}".format(args, stdout, stderr),
            level="debug",
        )
        return stdout.decode("utf-8").rstrip()

    def configure_keys(self):
        """Generate public and private keys."""
        self.migrate_keys()
        if self.charm_config.get("private-key"):
            # a key has been provided, store it
            private_key = self.charm_config.get("private-key")
            if self.kv.get("private-key") != private_key:
                self.kv.set("private-key", self.charm_config.get("private-key"))
        else:
            # key has not been provided, check if we have already generated one,
            # if not, generate one
            if self.kv.get("private-key"):
                log("Private key already configured", level="debug")
            else:
                log("Generating private key", level="debug")
                private_key = self.run_wg(["genkey"])
                self.kv.set("private-key", private_key)

        if not self.kv.get("public-key"):
            # Generate a public key for the configured/generated private key
            public_key = self.run_wg(["pubkey"], private_key.encode())
            self.kv.set("public-key", public_key)

    def configure(self):
        """Write configuration for WireGuard."""
        self.configure_keys()
        self.configure_forwarding()

        host.service('stop', self.service_name)
        peers_string = base64.b64decode(self.charm_config["peers"])
        peers_yaml = yaml.load(peers_string)
        context = {
            "private_key": self.kv.get("private_key"),
            "listen_port": self.charm_config["listen-port"],
            "peers": peers_yaml,
            "address": self.charm_config["address"],
            "forward": self.charm_config["forward-ip"],
            "forward_dev": self.charm_config["forward-dev"],
        }
        templating.render("wg0.conf.j2", self.cfg_file, context, perms=0o660)
        host.service("enable", self.service_name)
        host.service("start", self.service_name)

        self.configure_ports()
        hookenv.open_port(self.charm_config["listen-port"], protocol="UDP")

    def configure_ports(self):
        """Configure listening ports."""
        listen_port = self.charm_config["listen-port"]
        for open_port in hookenv.opened_ports():
            port, protocol = open_port.split("/")
            if protocol != 'udp' and port != listen_port:
                hookenv.close_port(port, protocol=protocol.upper())
        hookenv.open_port(self.charm_config["listen-port"], protocol="UDP")

    def configure_forwarding(self):
        """Disable ip forwarding in the kernel."""
        if self.charm_config['forward-ip']:
            sysctl_contents = "net.ipv4.ip_forward=1\nnet.ipv6.conf.all.forwarding=1"
            sysctl_file = open(self.sysctl_file, "w")
            sysctl_file.write(sysctl_contents)
            sysctl_file.close()
        else:
            os.remove(self.sysctl_file)

        cmd = ["sysctl", "--system"]
        try:
            check_call(cmd)
        except CalledProcessError as e:
            log("Failed to restore sysctl:", level="error")
            log("Cmd: {}".format(cmd), level="error")
            log("Error: {}".format(e.output), level="error")

    def get_config_action(self):
        """Retrieve and return settings and key data for get-config action."""
        with open(self.public_key_file, "r") as key:
            public_key = key.read().strip("\n")
        port = (self.charm_config["listen-port"],)
        ip = hookenv.unit_public_ip()
        return public_key, ip, port

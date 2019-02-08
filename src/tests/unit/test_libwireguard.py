#!/usr/bin/python3

import os


class TestLibwireguard():

    def test_pytest(self):
        assert True

    def test_wh(self, wh):
        ''' See if the wh fixture works to load charm configs '''
        assert isinstance(wh.charm_config, dict)

    # This only works with wg installed, TODO mock it or move tests to a
    # container
    def test_gen_keys(self, wh):
        ''' Verify keys are generated in key dir '''
        wh.gen_keys()
        assert os.path.exists(wh.key_dir + '/publickey')
        assert os.path.exists(wh.key_dir + '/privatekey')

    def test_write_config(self, wh):
        ''' Verify config template writes out '''
        wh.gen_keys()
        wh.write_config()
        assert os.path.exists(wh.cfg_file)
        with open(wh.cfg_file, 'r') as config:
            config_data = config.read()
        assert "10.10.10.1/24" in config_data
        assert "peer1key" in config_data
        assert "peer1ips" in config_data
        assert "peer1endpoint" in config_data
        assert "peer2key" in config_data
        assert "peer2ips" in config_data
        assert "PostUp" in config_data
        assert "PostDown" in config_data

        wh.charm_config['peers'] = ""
        wh.write_config()
        with open(wh.cfg_file, 'r') as config:
            config_data = config.read()
        assert "10.10.10.1/24" in config_data
        assert "peer1key" not in config_data
        assert "peer1ips" not in config_data
        assert "peer1endpoint" not in config_data
        assert "peer2key" not in config_data
        assert "peer2ips" not in config_data

    def test_enable_forward(self, wh, mock_ports):
        with open(wh.sysctl_file, 'r') as sysctl:
            settings = sysctl.read()
        assert "#net.ipv4.ip_forward=1" in settings
        assert "#net.ipv6.conf.all.forwarding=1" in settings
        wh.enable_forward()
        with open(wh.sysctl_file, 'r') as sysctl:
            settings = sysctl.read()
        assert "#net.ipv4.ip_forward=1" not in settings
        assert "#net.ipv6.conf.all.forwarding=1" not in settings
        assert "net.ipv4.ip_forward=1" in settings
        assert "net.ipv6.conf.all.forwarding=1" in settings

    def test_disable_forward(self, wh, mock_ports):
        wh.enable_forward()
        with open(wh.sysctl_file, 'r') as sysctl:
            settings = sysctl.read()
        assert "#net.ipv4.ip_forward=1" not in settings
        assert "#net.ipv6.conf.all.forwarding=1" not in settings
        assert "net.ipv4.ip_forward=1" in settings
        assert "net.ipv6.conf.all.forwarding=1" in settings
        wh.disable_forward()
        with open(wh.sysctl_file, 'r') as sysctl:
            settings = sysctl.read()
        assert "#net.ipv4.ip_forward=1" in settings
        assert "#net.ipv6.conf.all.forwarding=1" in settings

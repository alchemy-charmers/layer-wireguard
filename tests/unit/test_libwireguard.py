#!/usr/bin/python3
"""Unit tests for the wireguard helper library."""

import os


def test_pytest():
    """Test pytest."""
    assert True


def test_wh(wh):
    """Test the wh fixture to ensure loading of charm config works."""
    assert isinstance(wh.charm_config, dict)


def test_configure(wh):
    """Verify config template writes out."""
    wh.configure()
    assert os.path.exists(wh.cfg_file)
    with open(wh.cfg_file, "r") as config:
        config_data = config.read()
    assert "10.10.10.1/24" in config_data
    assert "peer1key" in config_data
    assert "peer1ips" in config_data
    assert "peer1endpoint" in config_data
    assert "peer2key" in config_data
    assert "peer2ips" in config_data
    assert "PostUp" in config_data
    assert "PostDown" in config_data

    wh.charm_config["peers"] = ""
    wh.configure()
    with open(wh.cfg_file, "r") as config:
        config_data = config.read()
    assert "10.10.10.1/24" in config_data
    assert "peer1key" not in config_data
    assert "peer1ips" not in config_data
    assert "peer1endpoint" not in config_data
    assert "peer2key" not in config_data
    assert "peer2ips" not in config_data


def test_forwarding(wh, mock_subprocess_check_call):
    """Test the IP forwarding functionality."""
    wh.charm_config["forward-ip"] = True
    wh.configure_forwarding()
    with open(wh.sysctl_file, "r") as sysctl:
        settings = sysctl.read()
    assert "net.ipv4.ip_forward=1" in settings
    assert "net.ipv6.conf.all.forwarding=1" in settings
    mock_subprocess_check_call.assert_called_with(["sysctl", "--system"])
    wh.charm_config["forward-ip"] = False
    wh.configure_forwarding()
    assert not os.path.isfile(wh.sysctl_file)
    mock_subprocess_check_call.assert_called_with(["sysctl", "--system"])

#!/usr/bin/python3
"""Test fixtures for the WireGuard charm."""
import pytest
import mock


@pytest.fixture
def mock_hookenv_config(monkeypatch):
    """Mock charm configuration."""
    import yaml

    def mock_config():
        cfg = {}
        yml = yaml.load(open("./config.yaml"))

        # Load all defaults
        for key, value in yml["options"].items():
            cfg[key] = value["default"]

        # # Manually add cfg from other layers
        # cfg['letsencrypt-domains'] = 'mock'
        return cfg

    monkeypatch.setattr("libwireguard.hookenv.config", mock_config)


@pytest.fixture
def mock_action_set(monkeypatch):
    """Mock action_set to facilitate testing of action results."""
    mocked_action_set = mock.Mock(returnvalue=True)
    monkeypatch.setattr("charmhelpers.core.hookenv.action_set", mocked_action_set)
    return mocked_action_set


@pytest.fixture
def mock_opened_ports(monkeypatch):
    """Mock the charmhelpers hookenv list of open ports."""
    def mocked_opened_ports_sa():
        return ['51902/udp', '11111/tcp', '22222/udp']

    mocked_opened_ports = mock.Mock()
    mocked_opened_ports.side_effect = mocked_opened_ports_sa
    monkeypatch.setattr('libwireguard.hookenv.opened_ports', mocked_opened_ports)
    return mocked_opened_ports


@pytest.fixture
def mock_open_port(monkeypatch):
    """Mock the open port call."""
    mocked_open_port = mock.Mock()
    monkeypatch.setattr('libwireguard.hookenv.open_port', mocked_open_port)
    return mocked_open_port


@pytest.fixture
def mock_close_port(monkeypatch):
    """Mock the close port call."""
    mocked_close_port = mock.Mock()
    monkeypatch.setattr('libwireguard.hookenv.close_port', mocked_close_port)
    return mocked_close_port


@pytest.fixture
def mock_service(monkeypatch):
    """Mock charmhelpers service control."""
    mocked_service = mock.Mock()
    monkeypatch.setattr('libwireguard.host.service', mocked_service)
    return mocked_service


@pytest.fixture
def mock_charm_dir(monkeypatch):
    """Mock charm working directory."""
    monkeypatch.setattr("libwireguard.hookenv.charm_dir", lambda: ".")


@pytest.fixture
def mock_render(monkeypatch):
    """Mock templating render function."""
    from functools import partial
    from charmhelpers.core import templating
    import getpass

    user = getpass.getuser()

    monkeypatch.setattr(
        "libwireguard.templating.render",
        partial(templating.render, owner=user, group=user),
    )


@pytest.fixture
def mock_subprocess_check_call(monkeypatch):
    """Mock calls to the check_call function."""
    mocked_check_call = mock.Mock()
    monkeypatch.setattr("libwireguard.check_call", mocked_check_call)
    return mocked_check_call


@pytest.fixture
def mock_subprocess_popen(monkeypatch):
    """Mock calls to the Popen function."""
    class MockedClassPopen():

        def __init__(self, args, stdin=None, stdout=None, stderr=None):
            return None

        def communicate(self, byteinput):
            return [b"mocked-stdout", b"mocked-stderr"]

    def mocked_sa_popen(cmd, stdin=None, stdout=None, stderr=None):
        return MockedClassPopen(cmd, stdin, stdout, stderr)

    mocked_popen = mock.Mock()
    mocked_popen.side_effect = mocked_sa_popen
    monkeypatch.setattr("libwireguard.Popen", mocked_popen)
    return mocked_popen


@pytest.fixture
def wh(
    tmpdir,
    mock_hookenv_config,
    monkeypatch,
    mock_charm_dir,
    mock_render,
    mock_subprocess_check_call,
    mock_subprocess_popen,
    mock_opened_ports,
    mock_service,
    mock_open_port,
    mock_close_port,
    mock_action_set,
):
    """Mock charm helper class."""
    import base64
    import shutil
    from libwireguard import WireguardHelper

    wh = WireguardHelper()

    # Use tmpdir
    wh.cfg_dir = str(tmpdir)
    wh.cfg_file = str(tmpdir.join("/wg0.cfg"))
    wh.sysctl_file = str(tmpdir.join("99-sysctl.conf"))
    shutil.copy("./tests/unit/99-sysctl.conf", wh.sysctl_file)

    with open("./tests/unit/peers.yaml", "rb") as peers:
        peers_options = base64.b64encode(peers.read()).decode("utf-8")
    wh.charm_config["peers"] = peers_options

    # Any other functions that load WH will get this version
    monkeypatch.setattr("libwireguard.WireguardHelper", lambda: wh)

    return wh

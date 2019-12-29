"""Functional tests for the WireGuard charm."""
import asyncio
import os
import pytest
import stat

# Treat tests as coroutines
pytestmark = [pytest.mark.asyncio]


juju_repository = os.getenv("JUJU_REPOSITORY", ".").rstrip("/")
series = [
    "xenial",
    "bionic",
    pytest.param("eoan", marks=pytest.mark.xfail(reason="canary")),
]
sources = [
    ("local", "{}/builds/wireguard".format(juju_repository)),
    ("jujucharms", "cs:~pirate-charmers/wireguard"),
]


# Custom fixtures
@pytest.fixture(params=series)
def series(request):
    """Return the series of the deployed application being tested."""
    return request.param


@pytest.fixture(params=sources, ids=[s[0] for s in sources])
def source(request):
    """Return the source of the app in test."""
    return request.param


@pytest.fixture
async def app(model, series, source):
    """Return the Juju application for the current test."""
    app_name = "wireguard-{}-{}".format(series, source[0])
    return model.applications[app_name]


async def test_wireguard_deploy(model, series, source, request):
    """Test the deployment of this charm for each combination of series and source."""
    # Starts a deploy for each series
    await model.deploy(
        "{}/builds/wireguard".format(juju_repository),
        series=series,
        application_name="wireguard-{}-{}".format(series, source[0]),
    )


async def test_wireguard_status(model, app, request, series):
    """Test the status of the deployed units and applications."""
    # Verifies status for all deployed series of the charm
    await model.block_until(lambda: app.status == "active")


@pytest.mark.timeout(120)
async def test_charm_upgrade(model, app, request):
    """Test upgrade of the juju charm store deployed charm to the local charm."""
    if app.name.endswith("local"):
        pytest.skip("No need to upgrade the local deploy")

    unit = app.units[0]
    await model.block_until(lambda: unit.agent_status == "idle")
    await asyncio.create_subprocess_shell(
        "juju upgrade-charm --switch={} -m {} {}".format(
            sources[0][1], model.info.name, app.name
        )
    )
    await model.block_until(
        lambda: unit.agent_status == "idle" or unit.agent_status == "error"
    )
    await model.block_until(lambda: app.status == "active" or app.status == "error")
    assert unit.agent_status != "error"
    assert app.status != "error"


async def test_get_config_action(app):
    """Run the get-config action."""
    unit = app.units[0]
    action = await unit.run_action("get-config")
    action = await action.wait()
    assert action.status == "completed"


async def test_run_command(app, jujutools):
    """Test running a known command on a deployed unit of the application."""
    unit = app.units[0]
    cmd = "hostname --all-ip-addresses"
    results = await jujutools.run_command(cmd, unit)
    assert results["Code"] == "0"
    assert unit.public_address in results["Stdout"]


async def test_file_stat(app, jujutools):
    """Test the presence of a known file on a deployed unit of the application."""
    unit = app.units[0]
    path = "/var/lib/juju/agents/unit-{}/charm/metadata.yaml".format(
        unit.entity_id.replace("/", "-")
    )
    fstat = await jujutools.file_stat(path, unit)
    assert stat.filemode(fstat.st_mode) == "-rw-r--r--"
    assert fstat.st_uid == 0
    assert fstat.st_gid == 0

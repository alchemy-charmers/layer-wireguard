"""Functional tests for the WireGuard charm."""
import os
import pytest

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

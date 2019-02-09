import os
import pytest
from juju.model import Model

# Treat tests as coroutines
pytestmark = pytest.mark.asyncio

series = ['xenial', 'bionic']
juju_repository = os.getenv('JUJU_REPOSITORY', '.').rstrip('/')


@pytest.fixture
async def model():
    model = Model()
    await model.connect_current()
    yield model
    await model.disconnect()


@pytest.fixture
async def apps(model):
    apps = []
    for entry in series:
        app = model.applications['wireguard-{}'.format(entry)]
        apps.append(app)
    return apps


@pytest.fixture
async def units(apps):
    units = []
    for app in apps:
        units.extend(app.units)
    return units


@pytest.mark.parametrize('series', series)
async def test_wireguard_deploy(model, series):
    # Starts a deploy for each series
    await model.deploy('{}/builds/wireguard'.format(juju_repository),
                       series=series,
                       application_name='wireguard-{}'.format(series))


# async def test_deploy_haproxy(model):
#     await model.deploy('cs:~pirate-charmers/haproxy',
#                        series='bionic',
#                        )


async def test_wireguard_status(apps, model):
    # Verifies status for all deployed series of the charm
    for app in apps:
        await model.block_until(lambda: app.status == 'active')


# async def test_add_relation(model, apps):
#     haproxy = model.applications['haproxy']
#     await model.block_until(lambda: haproxy.status == 'active')
#     port = 15821
#     for app in apps:
#         await app.set_config({'listen-port': str(port)})
#         port += 1
#         await app.add_relation('reverseproxy', 'haproxy:reverseproxy')
#         await model.block_until(lambda: haproxy.status == 'maintenance')
#         await model.block_until(lambda: haproxy.status == 'active')

# async def test_example_action(units):
#     for unit in units:
#         action = await unit.run_action('example-action')
#         action = await action.wait()
#         assert action.status == 'completed'

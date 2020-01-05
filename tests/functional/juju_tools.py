import base64
import pickle

import juju

# from juju.errors import JujuError


class JujuTools:
    def __init__(self, controller, model):
        self.controller = controller
        self.model = model

    async def run_command(self, cmd, target):
        """
        Runs a command on a unit.

        :param cmd: Command to be run
        :param unit: Unit object or unit name string
        """
        unit = (
            target
            if isinstance(target, juju.unit.Unit)
            else await self.get_unit(target)
        )
        action = await unit.run(cmd)
        return action.results

    async def remote_object(self, imports, remote_cmd, target):
        """
        Runs command on target machine and returns a python object of the result

        :param imports: Imports needed for the command to run
        :param remote_cmd: The python command to execute
        :param target: Unit object or unit name string
        """
        python3 = "python3 -c '{}'"
        python_cmd = (
            "import pickle;"
            "import base64;"
            "{}"
            'print(base64.b64encode(pickle.dumps({})), end="")'.format(
                imports, remote_cmd
            )
        )
        cmd = python3.format(python_cmd)
        results = await self.run_command(cmd, target)
        return pickle.loads(base64.b64decode(bytes(results["Stdout"][2:-1], "utf8")))

    async def file_stat(self, path, target):
        """
        Runs stat on a file

        :param path: File path
        :param target: Unit object or unit name string
        """
        imports = "import os;"
        python_cmd = 'os.stat("{}")'.format(path)
        print("Calling remote cmd: " + python_cmd)
        return await self.remote_object(imports, python_cmd, target)

    async def file_contents(self, path, target):
        """
        Returns the contents of a file

        :param path: File path
        :param target: Unit object or unit name string
        """
        cmd = "cat {}".format(path)
        result = await self.run_command(cmd, target)
        return result["Stdout"]

    async def service_status(self, service, target):
        """
        Returns status of a service on target unit

        :param service: Name of the service
        :param target: Unit object or unit name string
        """
        cmd = "systemctl status {}".format(service)
        result = await self.run_command(cmd, target)
        return result

    async def convert_config(self, config):
        """
        Converts config dictionary from get_config to one valid for set_config.
        """
        clean_config = {}
        for key, value in config.items():
            clean_config[key] = "{}".format(value['value'])
        return clean_config

    async def test_config(self, config, app, tests):
        """
        Verifies contents of files after a config change on an application.
        Application configuration will be reset to the original value even if an
        assertion fails.

        :param config: Dictionary containing application configuration to set
        :param app: The application to apply the config and verify files
        :param tests: A dictionary of tests. With the following keys
            path: path to the file to test
            contains (optional): assert this value is in the contents of path
            exclude (optional): assert this value is not in the contents of path
        """
        original_config = await self.convert_config(await app.get_config())
        unit0 = app.units[0]
        await app.set_config(config)
        # Wait for config to apply
        await self.model.block_until(lambda: unit0.agent_status == "executing")
        await self.model.block_until(lambda: unit0.agent_status == "idle")
        # Check the results
        for unit in app.units:
            for test in tests:
                path = test.get("path")
                contents = await self.file_contents(path, unit)
                print("Checking: {}".format(path))
                print("Contents: {}".format(contents))
                try:
                    expected_contents = test.get("contains", None)
                    if expected_contents:
                        assert expected_contents in contents
                    excluded_contents = test.get("exclude", None)
                    if excluded_contents:
                        assert excluded_contents not in contents
                except AssertionError:
                    # Reset configuration
                    await app.set_config(original_config)
                    # Wait for config to apply
                    await self.model.block_until(
                        lambda: unit0.agent_status == "executing"
                    )
                    await self.model.block_until(lambda: unit0.agent_status == "idle")
                    raise
        # Reset configuration
        await app.set_config(original_config)
        # Wait for config to apply
        await self.model.block_until(lambda: unit0.agent_status == "executing")
        await self.model.block_until(lambda: unit0.agent_status == "idle")

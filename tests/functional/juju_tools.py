"""Fixtures for functional testing of Juju charms."""
import base64
import pickle

import juju

# from juju.errors import JujuError


class JujuTools:
    """Provide fixtures as a single class for ease of use."""

    def __init__(self, controller, model):
        """Initialise controller and model based on use as a fixture."""
        self.controller = controller
        self.model = model

    # async def get_app(self, name):
    #     """Returns the application requested"""
    #     app = None
    #     try:
    #         app = self.model.applications[name]
    #     except KeyError:
    #         raise JujuError("Cannot find application {}".format(name))
    #     return app

    # async def get_unit(self, name):
    #     """Returns the requested <app_name>/<unit_number> unit"""
    #     unit = None
    #     try:
    #         (app_name, unit_number) = name.split('/')
    #         unit = self.model.applications[app_name].units[unit_number]
    #     except (KeyError, ValueError):
    #         raise JujuError("Cannot find unit {}".format(name))
    #     return unit

    # async def get_entity(self, name):
    #     """Returns a unit or an application"""
    #     entity = None
    #     try:
    #         entity = await self.get_unit(name)
    #     except JujuError:
    #         try:
    #             entity = await self.get_app(name)
    #         except JujuError:
    #             raise JujuError("Cannot find entity {}".format(name))
    #     return entity

    async def run_command(self, cmd, target):
        """
        Run a command on a unit.

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
        Run command on target machine and returns a python object of the result.

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
        Run stat on a file via remote python call.

        :param path: File path
        :param target: Unit object or unit name string
        """
        imports = "import os;"
        python_cmd = 'os.stat("{}")'.format(path)
        print("Calling remote cmd: " + python_cmd)
        return await self.remote_object(imports, python_cmd, target)

    async def file_contents(self, path, target):
        """
        Return the contents of a file.

        :param path: File path
        :param target: Unit object or unit name string
        """
        cmd = "cat {}".format(path)
        result = await self.run_command(cmd, target)
        return result["Stdout"]

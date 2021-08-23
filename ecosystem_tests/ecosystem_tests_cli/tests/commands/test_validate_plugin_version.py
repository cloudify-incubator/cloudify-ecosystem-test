from mock import patch

from ..commands import BaseCliCommandTest
from ...commands.validate_plugin_version import validate_plugin_version
from ...constants import DEFAULT_DIRECTORY_PATH

from os import path, pardir

mock_plugin = path.join(
    path.abspath(
        path.join(
            path.dirname(__file__),
            pardir)
    ),
    'mock_plugin'
)


class ValidatePluginVersionTest(BaseCliCommandTest):

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands'
           '.validate_plugin_version.validate')
    def test_validate_default_values(self,
                                     mock_validate_plugin_version,
                                     mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(validate_plugin_version, ['-d', mock_plugin])
        # raise Exception(mock_validate_plugin_version.__dict__)
        mock_validate_plugin_version.assert_called_once_with(mock_plugin)

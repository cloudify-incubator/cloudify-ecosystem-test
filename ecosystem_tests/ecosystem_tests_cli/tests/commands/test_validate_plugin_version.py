from mock import patch

from ..commands import BaseCliCommandTest
from ...commands.validate_plugin_version import validate_plugin_version
from ...constants import DEFAULT_DIRECTORY_PATH


class ValidatePluginVersionTest(BaseCliCommandTest):

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands'
           '.validate_plugin_version.validate_plugin_version')
    def test_validate_default_values(self,
                                     mock_validate_plugin_version,
                                     mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(validate_plugin_version, [])
        mock_validate_plugin_version.assert_called_once_with()

        # mock_validate_plugin_version.assert_called_once_with(
        #    plugin_version_file_name=DEFAULT_DIRECTORY_PATH,
        #    plugin_version_id=self.test_id)

from mock import patch

from .commands import BaseCliCommandTest
from ..ecosystem_tests_cli.commands.validate_plugin_version import validate_plugin_version  # noqa

from os import path, pardir, environ

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
        if 'CIRCLE_BRANCH' not in environ:
            environ['CIRCLE_BRANCH'] = '0.0.0-build'
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(validate_plugin_version, ['-d', mock_plugin])
        mock_validate_plugin_version.assert_called_once_with(
            mock_plugin, environ['CIRCLE_BRANCH'])

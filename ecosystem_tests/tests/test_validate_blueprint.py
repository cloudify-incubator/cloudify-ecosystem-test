from mock import patch

from .commands import BaseCliCommandTest
from ..ecosystem_tests_cli.commands.validate_blueprint import validate_blueprint  # noqa
from ..ecosystem_tests_cli.constants import DEFAULT_BLUEPRINT_PATH


class ValidateBlueprintTest(BaseCliCommandTest):

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.validate_blueprint'
           '.blueprint_validate')
    def test_validate_default_values(self,
                                     mock_blueprint_validate,
                                     mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(validate_blueprint, [])
        mock_blueprint_validate.assert_called_once_with(
            blueprint_file_name=DEFAULT_BLUEPRINT_PATH,
            blueprint_id=self.test_id)

    @patch('ecosystem_tests.ecosystem_tests_cli.utilities.id_generator')
    @patch('ecosystem_tests.ecosystem_tests_cli.commands.validate_blueprint'
           '.blueprint_validate')
    def test_validate_multiple_blueprints(self,
                                          mock_blueprint_validate,
                                          mock_id_generator):
        mock_id_generator.return_value = self.test_id
        self.runner.invoke(validate_blueprint, ['-b',
                                                '/path/to/blueprint1.yaml',
                                                '-b',
                                                '/path/to/blueprint2.yaml'])
        self.assertEqual(mock_blueprint_validate.call_count, 2)
        mock_blueprint_validate.assert_any_call(
            blueprint_file_name='/path/to/blueprint1.yaml',
            blueprint_id=self.test_id)
        mock_blueprint_validate.assert_any_call(
            blueprint_file_name='/path/to/blueprint2.yaml',
            blueprint_id=self.test_id)

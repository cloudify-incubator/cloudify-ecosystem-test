import os
import tempfile
import unittest

from ..validations import check_is_latest_version


class CheckIsMaxVersion(unittest.TestCase):
    def test_valid_input(self):
        dict_version = ['1.4.2', '1.4.3', '1.4.4', '1.4.5', '1.4.6', '1.4.7',
                        '1.4.8', '1.4.9', '1.4.10', '1.4.11', '1.4.12',
                        '1.4.13', '1.5', '1.5.1', '1.5.1.1', '1.5.1.2', '2.0.0',
                        '2.0.1', '2.0.2', '2.1.0', '2.2.0', '2.2.1', '2.3.0',
                        '2.3.1', '2.3.2', '2.3.3', '2.3.4', '2.3.5', '2.4.0',
                        '2.4.1', '2.4.2', '2.4.3', '2.4.4', '2.5.0', '2.5.1',
                        '2.5.2', '2.5.3', '2.5.4', '2.5.5', '2.5.6', '2.5.7',
                        '2.5.8', '2.5.9', '2.5.10', '2.5.11', '2.5.12',
                        '2.5.13', '2.5.14', '2.6.0', '2.7.0', '2.8.0', '2.9.0',
                        '2.9.1', '2.9.2', '2.11.0', '2.11.1', '2.12.0',
                        '2.12.1', '2.12.2', '2.12.4', '2.12.3']

        version_to_check = '2.12.2'
        f = tempfile.NamedTemporaryFile(
            dir=os.path.expanduser('~'), delete=False)
        f.close()

        for version_number in dict_version:
            tf = open(f.name, 'a')
            tf.write('{}: blablalba\n'.format(version_number))
            tf.close()

            if version_number == version_to_check:
                self.assertTrue(
                    check_is_latest_version(version_to_check, f.name))
            else:
                self.assertFalse(
                    check_is_latest_version(version_to_check, f.name))

        os.remove(f.name)

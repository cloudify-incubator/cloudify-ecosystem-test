


import unittest

from ..packaging import update_assets_in_plugin_dict


class TestPackaging(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_update_assets_in_plugin_dict(self):
        assets = [
            'new-centos-altarch.wgn',
            'new-centos-altarch.wgn.md5',
            'new-centos-Core.wgn',
            'new-centos-Core.wgn.md5',
        ]
        wagons_list = [
            {
                'name': 'Centos AltArch',
                'md5url': 'old-centos-altarch.wgn.md5',
                'url': 'old-centos-altarch.wgn',
            },
            {
                'name': 'Centos Core',
                'md5url': 'old-centos-Core.wgn.md5',
                'url': 'old-centos-Core.wgn',
            },
            {
                'name': 'Redhat Maipo',
                'md5url': 'old-redhat-maipo.wgn.md5',
                'url': 'old-redhat-maipo.wgn',
            },
        ]
        plugin_dict = {
            'link': 'https:/foo/taco/izam',
            'version': 'wgn',
            'wagons': wagons_list
        }
        expected = [
            {
                'name': 'Centos AltArch',
                'md5url': 'new-centos-altarch.wgn.md5',
                'url': 'new-centos-altarch.wgn',
            },
            {
                'name': 'Centos Core',
                'md5url': 'new-centos-Core.wgn.md5',
                'url': 'new-centos-Core.wgn',
            },
            {
                'name': 'Redhat Maipo',
                'md5url': 'old-redhat-maipo.wgn.md5',
                'url': 'old-redhat-maipo.wgn',
            },
        ]
        update_assets_in_plugin_dict(plugin_dict, assets, 'wgn')
        print(plugin_dict['wagons'])
        print(expected)
        self.assertListEqual(plugin_dict['wagons'], sorted(
            expected, key=lambda d: d['name']))

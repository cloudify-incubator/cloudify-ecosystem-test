
from copy import deepcopy

from .s3 import (
    URL_TEMPLATE,
    get_objects_in_key)

from .logging import logger

CORE_INDEX = 0
ALTARCH_INDEX = 1
MAIPO_INDEX = 2

CORE_ID = 'centos-Core'
ALTARCH_ID = 'centos-altarch'
MAIPO_ID = 'redhat-Maipo'


def get_wagons_list(plugin_name, plugin_version):
    wagons_list = deepcopy(WAGONS_LIST_TEMPLATE)
    plugin_version_objects = get_objects_in_key(
        plugin_name,
        plugin_version
    )
    total_objects = len(plugin_version_objects)
    for i in range(0, total_objects):
        if i + 2 >= total_objects:
            break
        if plugin_version not in plugin_version_objects[i] and \
                plugin_version not in plugin_version_objects[i + 1]:
            continue
        if plugin_version_objects[i].endswith('.wgn') and \
                plugin_version_objects[i + 1].endswith('.wgn.md5'):

            url = URL_TEMPLATE.format(
                *plugin_version_objects[i].split('/')[-3:])

            md5url = URL_TEMPLATE.format(
                *plugin_version_objects[i + 1].split('/')[-3:])

            wagon_dict = {
                'url': url,
                'md5url': md5url
            }

            if CORE_ID in url and CORE_ID in md5url:
                wagons_list[CORE_INDEX].update(wagon_dict)
            if ALTARCH_ID in url and ALTARCH_ID in md5url:
                wagons_list[ALTARCH_INDEX].update(wagon_dict)
            if MAIPO_ID in url and MAIPO_ID in md5url:
                wagons_list[MAIPO_INDEX].update(wagon_dict)

    return wagons_list


JSON_TEMPLATE = [
    {
        "description": "A Cloudify Plugin that provisions resources in AWS",
        "releases": "https://github.com/cloudify-cosmo/cloudify-aws-plugin/releases",
        "title": "AWS",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/aws-1.png",
        "name": "cloudify-aws-plugin",
        "yaml": None
    },
    {
        "description": "A Cloudify Plugin that provisions resources in Microsoft Azure",
        "releases": "https://github.com/cloudify-cosmo/cloudify-azure-plugin/releases",
        "title": "Azure",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/azurelogo.png",
        "name": "cloudify-azure-plugin",
        "yaml": None
    },
    {
        "description": "A Cloudify Plugin that provisions resources in StarlingX",
        "releases": "https://github.com/cloudify-cosmo/cloudify-starlingx-plugin/releases",
        "title": "StarlingX",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2021/05/starling.png",
        "name": "cloudify-starlingx-plugin",
        "yaml": None
    },
    {
        "description": "A Cloudify Plugin that provisions resources in Google Cloud Platform",
        "releases": "https://github.com/cloudify-cosmo/cloudify-gcp-plugin/releases",
        "title": "GCP",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/gcplogo.png",
        "name": "cloudify-gcp-plugin",
        "yaml": None
    },
    {
        "description": "A Cloudify Plugin that provisions resources in OpenStack using the OpenStack SDK. Note, this plugin is not compatible with the OpenStack plugin.",
        "releases": "https://github.com/cloudify-cosmo/cloudify-openstack-plugin/releases",
        "title": "OpenStackV3",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/oslogo.png",
        "name": "cloudify-openstack-plugin",
        "yaml": None
    },
    {
        "description": "A Cloudify Plugin that provisions resources in VMware vSphere",
        "releases": "https://github.com/cloudify-cosmo/cloudify-vsphere-plugin/releases",
        "title": "vSphere",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/vsphere.png",
        "name": "cloudify-vsphere-plugin",
        "yaml": None
    },
    {
        "description": "Deploy and manage Cloud resources with Terraform.",
        "releases": "https://github.com/cloudify-cosmo/cloudify-terraform-plugin/releases",
        "title": "Terraform",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2020/07/terraform-icon.png",
        "name": "cloudify-terraform-plugin",
        "yaml": None
    },
    {
        "description": "Deploy and manage Cloud resources with Terragrunt.",
        "releases": "https://github.com/cloudify-cosmo/cloudify-terragrunt-plugin/releases",
        "title": "Terragrunt",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2020/07/terragrunt-icon.png",
        "name": "cloudify-terragrunt-plugin",
        "yaml": None
    },
    {
        "description": "The Ansible plugin can be used to run Ansible Playbooks",
        "releases": "https://github.com/cloudify-cosmo/cloudify-ansible-plugin/releases",
        "title": "Ansible",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2020/07/ansible-icon.png",
        "name": "cloudify-ansible-plugin",
        "yaml": None
    },
    {
        "description": "Cloudify plugin for packaging Kubernetes microservices in Cloudify blueprints",
        "releases": "https://github.com/cloudify-cosmo/cloudify-kubernetes-plugin/releases",
        "title": "Kubernetes",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2020/07/kube-icon.png",
        "name": "cloudify-kubernetes-plugin",
        "yaml": None
    },
    {
        "description": "Add direct support of Docker to cloudify.",
        "releases": "https://github.com/cloudify-cosmo/cloudify-docker-plugin/releases",
        "title": "Docker",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2020/05/docker-icon.png",
        "name": "cloudify-docker-plugin",
        "yaml": None
    },
    {
        "description": "Cloudify plugin for serializing TOSCA node templates to netconf configuration",
        "releases": "https://github.com/cloudify-cosmo/cloudify-netconf-plugin/releases",
        "title": "Netconf",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/netconf-150x150.png",
        "name": "cloudify-netconf-plugin",
        "yaml": None
    },
    {
        "description": "For running fabric tasks or commands from the manager",
        "releases": "https://github.com/cloudify-cosmo/cloudify-fabric-plugin/releases",
        "title": "Fabric",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/fabriclogo-150x117.png",
        "name": "cloudify-fabric-plugin",
        "yaml": None
    },
    {
        "description": "Add direct support of libvirt to cloudify, use with restrictions",
        "releases": "https://github.com/cloudify-incubator/cloudify-libvirt-plugin/releases",
        "title": "Libvirt",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2018/09/libvirt.png",
        "name": "cloudify-libvirt-plugin",
        "yaml": None
    },
    {
        "description": "Various extension utilities, including REST API",
        "releases": "https://github.com/cloudify-incubator/cloudify-utilities-plugin/releases",
        "title": "Utilities",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/pluginlogo.png",
        "name": "cloudify-utilities-plugin",
        "yaml": None
    },
    {
        "description": "The Host Pool Service is a Python 2 RESTful web service built on flask-restful",
        "releases": "https://github.com/cloudify-cosmo/cloudify-host-pool-plugin/releases",
        "title": "HOST-POOL",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/pluginlogo.png",
        "name": "cloudify-host-pool-plugin",
        "yaml": None
    },
    {
        "description": "OpenStack (v2): A Cloudify Plugin that provisions resources in OpenStack using the OpenStack APIs. (deprecated).",
        "releases": "https://github.com/cloudify-cosmo/cloudify-openstack-plugin/releases",
        "title": "OpenStack",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/oslogo.png",
        "name": "cloudify-openstack-plugin",
        "yaml": None
    },
    {
        "description": "A Cloudify plugin that provisions resources in VMware vCloud (deprecated - supports vCloud Director 9.7 or later)",
        "releases": "https://github.com/cloudify-cosmo/cloudify-vcloud-plugin/releases",
        "title": "vCloud",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2019/08/vsphere.png",
        "name": "cloudify-vcloud-plugin",
        "yaml": None
    },
    {
        "description": "Cloudify Helm 3 plugin",
        "releases": "https://github.com/cloudify-incubator/cloudify-helm-plugin/releases",
        "title": "Helm",
        "version": None,
        "link": None,
        "wagons": [],
        "icon": "https://cloudify.co/wp-content/uploads/2020/11/helm-icon.png",
        "name": "cloudify-helm-plugin",
        "yaml": None
    }
]

WAGONS_LIST_TEMPLATE = [
    {
        "name": "Centos Core",
        "url": None,
        "md5url": None,
    },
    {
        "name": "Centos AltArch",
        "url": None,
        "md5url": None,
    },
    {
        "name": "Redhat Maipo",
        "url": None,
        "md5url": None,
    },
]

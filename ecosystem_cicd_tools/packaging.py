
from __future__ import with_statement

import shutil
import logging
import zipfile
from hashlib import md5
from os import path, walk, listdir
from tempfile import NamedTemporaryFile


def md5sum(filename, buf_size=8192):
    # https://sebest.github.io/post/a-quick-md5sum-equivalent-in-python/
    m = md5()
    md5_filename = '{original}.md5'.format(original=filename)
    with open(filename, 'b') as infile:
        data = infile.read(buf_size)
        while data:
            m.update(data)
            data = infile.read(buf_size)
    with open(md5_filename, 'wb') as outfile:
        outfile.write(m.hexdigest)
    return md5_filename


def get_workspace_files():
    workspace_path = path.join(path.abspath('workspace'), 'build')
    files = []
    for f in listdir(workspace_path):
        files.append(f)
        if f.endswith('.wgn'):
            files.append(md5sum(f))
    return [f for f in listdir(workspace_path)]


def package_blueprint(name, source_directory):
    archive_temp = NamedTemporaryFile(delete=False)
    if '/' in name:
        name = name.replace('/', '-')
        name = name.strip('-')
    destination = path.join(
        path.dirname(archive_temp.name), '{0}.zip'.format(name))
    create_archive(source_directory, archive_temp.name)
    logging.info('Moving {0} to {1}.'.format(archive_temp.name, destination))
    shutil.move(archive_temp.name, destination)
    return destination


def create_archive(source_directory, destination):
    logging.info(
        'Packaging archive from source: {0} to destination: {1}.'.format(
            source_directory, destination))
    zip_file = zipfile.ZipFile(destination, 'w')
    for root, _, files in walk(source_directory):
        for filename in files:
            logging.info('Packing {0} in archive.'.format(filename))
            file_path = path.join(root, filename)
            source_dir = path.dirname(source_directory)
            zip_file.write(
                file_path, path.relpath(file_path, source_dir))
    zip_file.close()
    logging.info('Finished writing archive {0}'.format(destination))

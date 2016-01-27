#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "docker_manage",
    version = "0.1.11",
    author = ["Mateusz Żółtak", "Omar Siam"],
    author_email = ["mateusz.zoltak@oeaw.ac.at", "omar.siam@oeaw.ac.at"],
    description = ("Tools to manage docker instances and reverse proxying to them."),
    license = "BSD",
    keywords = "docker apache managent",
    url = "",
    packages=['docker_manage', "docker_manage.Environments"],
    scripts=['docker-manage'],
    data_files=[('/usr/sbin', ['docker-manage-admin', 'docker-add-project', 'docker-check-quota',
                           'docker-clean', 'docker-install-container', 'docker-mount-volumes',
                           'docker-register-proxy', 'docker-register-systemd', 'docker-remove-unused-containers',
                           'docker-remove-unused-images']),
                ('/etc/sudoers.d', ['etc/sudoers.d/docker'])
                ],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)

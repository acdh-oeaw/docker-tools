#!/usr/bin/python
# -*- coding: UTF-8 -*-
import os
import time
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "docker_manage",
    version = time.time(),
    author = ["Mateusz Żółtak", "Omar Siam"],
    author_email = ["mateusz.zoltak@oeaw.ac.at", "omar.siam@oeaw.ac.at"],
    description = ("Tools to manage docker instances and reverse proxying to them."),
    license = "BSD",
    keywords = "docker apache managent",
    url = "",
    packages=['docker_manage', "docker_manage.Environments"],
    scripts=['scripts/docker-manage'],
    data_files=[
        (
            '/usr/sbin', 
            [
                'docker-manage-admin', 'scripts/docker-add-project',
                'scripts/docker-check-quota', 'scripts/docker-clean', 'scripts/docker-register-proxy', 
                'scripts/docker-register-systemd', 'scripts/docker-remove-unused-containers', 
                'scripts/docker-remove-unused-images', 'scripts/docker-remove-project', 
                'scripts/docker-build-images', 'scripts/docker-tools-update', 'scripts/docker-systemctl', 
                'scripts/docker-collect-stats', 'scripts/docker-collect-apache-logs'
            ]
        )
    ],
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)

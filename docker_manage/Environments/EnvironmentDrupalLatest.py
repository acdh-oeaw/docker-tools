import codecs
import os
import re
from . import *


class EnvironmentDrupalLatest(EnvironmentDrupal9, IEnvironment):
    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = 'http_drupal_latest'
        super(EnvironmentDrupalLatest, self).__init__(conf, owner)


import codecs
import re
from . import *


class EnvironmentJS(EnvironmentApache, IEnvironment):
    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = 'js'
        super(EnvironmentJS, self).__init__(conf, owner)


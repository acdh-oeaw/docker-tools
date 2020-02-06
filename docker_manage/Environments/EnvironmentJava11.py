import os

from . import *

class EnvironmentJava11(EnvironmentJava8, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'java11'
    super(EnvironmentJava11, self).__init__(conf, owner)

class EnvironmentJava9(EnvironmentJava8, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'java11'
    super(EnvironmentJava11, self).__init__(conf, owner)

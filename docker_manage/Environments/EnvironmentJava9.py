import os

from . import *

class EnvironmentJava9(EnvironmentJava8, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'java9'
    super(EnvironmentJava9, self).__init__(conf, owner)

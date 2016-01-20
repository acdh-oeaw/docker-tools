from . import *

class EnvironmentPHP(EnvironmentApache, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_php'
    super(EnvironmentPHP, self).__init__(conf, owner)


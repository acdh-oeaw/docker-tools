from . import *
from ..Param import Param

class Environmentcrxqmets(EnvironmenteXistdb30, IEnvironment):

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'cr-xq-mets'
    super(Environmentcrxqmets, self).__init__(conf, owner)

class EnvironmentRHELcrxqmets(Environmentcrxqmets, IEnvironment):

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'rhel_cr-xq-mets'
    super(EnvironmentRHELcrxqmets, self).__init__(conf, owner)
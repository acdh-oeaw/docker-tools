from . import *
from ..Param import Param

class EnvironmentRHELcrxqmets(EnvironmentHTTP, IEnvironment):

  def __init__(self, conf, owner):
    self.runAsUser = True
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'rhel_cr-xq-mets'
    super(EnvironmentRHELcrxqmets, self).__init__(conf, owner)

class Environmentcrxqmets(EnvironmentHTTP, IEnvironment):

  def __init__(self, conf, owner):
    self.runAsUser = True
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'cr-xq-mets'
    super(Environmentcrxqmets, self).__init__(conf, owner)
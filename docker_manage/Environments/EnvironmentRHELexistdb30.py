from . import *
from ..Param import Param

class EnvironmentRHELexistdb30(EnvironmentHTTP, IEnvironment):

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'rhel_existdb30'
    super(EnvironmentRHELexistdb30, self).__init__(conf, owner)
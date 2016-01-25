from . import *
from ..Param import Param

class EnvironmentRHELJDK78(EnvironmentHTTP, IEnvironment):

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'rhel_jdk7_8'
    super(EnvironmentRHELJDK78, self).__init__(conf, owner)
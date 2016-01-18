from . import *
from ..Param import Param

class EnvironmentRHELJava8(EnvironmentHTTP, IEnvironment):

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = '_rhel_java8'
    super(EnvironmentRHELJava8, self).__init__(conf, owner)

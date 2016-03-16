from . import *

class Environmentcorpus_shell(EnvironmentPHP, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = self.DockerfileDir
    super(Environmentcorpus_shell, self).__init__(conf, owner)
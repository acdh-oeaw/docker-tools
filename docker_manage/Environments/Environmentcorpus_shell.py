from . import *

class Environmentcorpus_shell(EnvironmentPHP, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'corpus_shell'
    super(Environmentcorpus_shell, self).__init__(conf, owner)
    if self.LogDir is None:
      raise Exception('LogDir is required for this environment. It is missing or invalid')
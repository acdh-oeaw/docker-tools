class EnvironmentDrupal7(EnvironmentPHP, IEnvironment):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_drupal7'
    super(EnvironmentDrupal6, self).__init__(conf, owner)


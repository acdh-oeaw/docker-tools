class EnvironmentWSGI2(EnvironmentWSGI3):
  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_wsgi2'
    super(EnvironmentWSGI2, self).__init__(conf, owner)


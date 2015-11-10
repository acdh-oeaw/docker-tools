class EnvironmentDrupal7(EnvironmentPHP, IEnvironment):
  skipDocumentRoot = True

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'http_drupal7'

    super(EnvironmentDrupal7, self).__init__(conf, owner)

    if self.HTTPS == "true" :
      self.guestVHTemplate = self.guestVHTemplate.replace('<VirtualHost *:80>', '<VirtualHost *:80>\n' + self.guestVHTemplateSSL)

    if not 'SiteDir' in conf or not Param.isValidRelPath(conf['SiteDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['SiteDir']) :
      raise Exception('SiteDir is missing or invalid')
    self.Mounts.append({ "Host" : conf['SiteDir'], "Guest" : '/var/www/html/sites/default', "Rights" : "rw" })

    if not 'AllDir' in conf or not Param.isValidRelPath(conf['AllDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['AllDir']) :
      raise Exception('AllDir is missing or invalid')
    self.Mounts.append({ "Host" : conf['AllDir'], "Guest" : '/var/www/html/sites/all', "Rights" : "rw" })
    
  # as Drupal environment does not have DocumentRoot it is not clear what
  # should be a base dir for aliases
  def processAliases(self, conf):
    pass

  def runHooks(self, verbose):
    super(EnvironmentDrupal7, self).runHooks(verbose)

    if verbose :
      print '    Setting up drupal permissions'
    self.runProcess(['docker', 'exec', self.Name, 'chown', '-R', 'user:user', '/var/www/html'], verbose, '', 'Setting up permissions failed')

  guestVHTemplateSSL = """
  SetEnv HTTPS on
  SetEnv REQUEST_SCHEME https
  SetEnv protossl s
"""



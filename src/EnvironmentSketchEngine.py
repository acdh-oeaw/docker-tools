class EnvironmentSketchEngine(EnvironmentHTTP, IEnvironment):
  DataDir     = ''
  RegistryDir = ''
  SkeDir      = ''
  Corplist    = None

  def __init__(self, conf, owner):
    self.Corplist = []

    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'sketch-engine'
    if 'UserName' not in conf :
      conf['UserName'] = 'apache'
    super(EnvironmentSketchEngine, self).__init__(conf, owner)

    if (
      'DataDir' not in conf
      or self.owner and (
           not isinstance(conf['DataDir'], basestring) 
        or not Param.isValidRelPath(conf['DataDir']) 
        or not Param.isValidDir(self.BaseDir + '/' + conf['DataDir']) 
      )
    ) :
      raise Exception('DataDir is missing or invalid')
    self.DataDir = conf['DataDir']

    if (
      'RegistryDir' not in conf
      or self.owner and (
           not isinstance(conf['RegistryDir'], basestring) 
        or not Param.isValidRelPath(conf['RegistryDir']) 
        or not Param.isValidDir(self.BaseDir + '/' + conf['RegistryDir']) 
      )
    ) :
      raise Exception('RegistryDir is missing or invalid')
    self.RegistryDir = conf['RegistryDir']


    if (
      'SkeDir' not in conf
      or self.owner and (
           not isinstance(conf['SkeDir'], basestring) 
        or not Param.isValidRelPath(conf['SkeDir']) 
        or not Param.isValidDir(self.BaseDir + '/' + conf['SkeDir']) 
      )
    ) :
      raise Exception('SkeDir is missing or invalid')
    self.SkeDir = conf['SkeDir']

    if 'Corplist' in conf :
      if not isinstance(conf['Corplist'], list) :
        if not isinstance(conf['Corplist'], basestring) :
          raise Exception('Corplist is not a string nor list')
        conf['Corplist'] = [conf['Corplist']]
      for corpora in conf['Corplist'] :
        if self.owner and (not Param.isValidDir(self.BaseDir + '/' + self.DataDir + '/' + corpora)) :
          raise Exception(corpora + ' corpora subdir is missing in the DataDir')
        if self.owner and (not Param.isValidFile(self.BaseDir + '/' + self.RegistryDir + '/' + corpora)) :
          raise Exception(corpora + ' corpora configuration file is missing in the RegistryDir')
        self.Corplist.append(corpora)
    if len(self.Corplist) == 0 :
      print '    Corplist is empty - bonito will not work.\n    Create a corpora, fill in the Corplist configuration property and rerun environment to make bonito work.'

    self.Mounts.append({"Host" : self.SkeDir,      "Guest" : "/var/lib/ske",          "Rights" : "rw"})
    self.Mounts.append({"Host" : self.RegistryDir, "Guest" : "/var/lib/ske/registry", "Rights" : "rw"})
    self.Mounts.append({"Host" : self.RegistryDir, "Guest" : "/corpora/registry",     "Rights" : "rw"})
    self.Mounts.append({"Host" : self.DataDir,     "Guest" : "/corpora/data",         "Rights" : "rw"})
    self.Ports = [{ "Host" : HTTPReverseProxy.getPort(), "Guest" : 80 , "Type" : "HTTP", "ws" : [], "Alias" : ""}]

  def runHooks(self, verbose):
    super(EnvironmentSketchEngine, self).runHooks(verbose)

    if verbose :
      print '    Reconfiguring /var/www/bonito/run.cgi'
    replace1 = "s/^ *corplist = .*$/    corplist = [u'" + "', u'".join(self.Corplist) + "']/"
    replace2 = "s/^ *corpname = .*$/    corpname = u'" + (self.Corplist[0] if len(self.Corplist) > 0 else '') + "'/"
    self.runProcess(['docker', 'exec', self.Name, 'sed', '-i', '-e', replace1, '-e', replace2, '/var/www/bonito/run.cgi'], False, '', '/var/www/bonito/run.cgi update failed')

    if verbose :
      print '    Adjusting files ownership'
    self.runProcess(['docker', 'exec', self.Name, 'chown', '-R', 'apache:apache', '/var/www/bonito', '/var/lib/ske', '/usr/share/httpd'], False, '', 'ownership adjustment failed')

    if verbose :
      print '    Preparing SkeDir'
    for directory in ['cache', 'jobs', 'options', 'subcorp']:
      if not os.path.isdir(self.BaseDir + '/' + self.SkeDir + '/' + directory) :
        os.mkdir(self.BaseDir + '/' + self.SkeDir + '/' + directory)
    if not os.path.isfile(self.BaseDir + '/' + self.SkeDir + '/htpasswd') :
      os.mknod(self.BaseDir + '/' + self.SkeDir + '/htpasswd')


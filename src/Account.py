class Account:
  base         = '/home'
  name         = ''
  uid          = -1
  gid          = -1
  environments = None
  owner        = False

  def __init__(self, name):
    self.environments = []

    if not Param.isValidName(name) :
      raise Exception('account name contains forbidden characters')
    self.name = name
    path = self.base + '/' + self.name
    if not Param.isValidDir(path) :
      raise Exception('account does not exist')
    self.uid = os.stat(path).st_uid
    self.gid = os.stat(path).st_gid

    self.owner = os.access(path, os.W_OK)
  
  def readConfig(self):
    print '  ' + self.name
    confFileName = self.base + '/' + self.name + '/config.json'
    if os.path.isfile(confFileName):
      try:
        config = json.load(open(confFileName, 'r'))
        self.processConfig(config)
      except Exception as e:
        print '  Configuration file ' + confFileName + ' is not a valid JSON: ' + str(e)

  def processConfig(self, conf):
    if not isinstance(conf, list) :
      raise Exception('configuration is not a list')

    self.environments = []
    for envConf in conf:
      try:
        envConf['BaseDir'] = self.base + '/' + self.name
        envConf['UID']     = self.uid
        envConf['GID']     = self.gid
        envConf['Account'] = self.name
        if 'Type' in envConf :
          if   envConf['Type'] == 'HTTP' :
            env = EnvironmentHTTP(envConf, self.owner)
          elif envConf['Type'] == 'Apache' :
            env = EnvironmentApache(envConf, self.owner)
          elif envConf['Type'] == 'PHP' :
            env = EnvironmentPHP(envConf, self.owner)
          elif envConf['Type'] == 'WSGI3' :
            env = EnvironmentWSGI3(envConf, self.owner)
          elif envConf['Type'] == 'WSGI2' :
            env = EnvironmentWSGI2(envConf, self.owner)
          elif envConf['Type'] == 'Drupal6' :
            env = EnvironmentDrupal6(envConf, self.owner)
          elif envConf['Type'] == 'Generic' :
            env = Environment(envConf, self.owner)
          elif envConf['Type'] == 'noske' :
            env = EnvironmentNoske(envConf, self.owner)
          elif envConf['Type'] == 'noskePatched' :
            env = EnvironmentNoskePatched(envConf, self.owner)
          else :
            raise Exception('environment is of unsupported type (' + envConf['Type'] + ')')
        else :
          raise Exception('environment has no type')
        self.environments.append(env)
      except Exception as e:
        print '  Error in ', (1 + len(self.environments)), ' environment: ', e

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = {}
    for env in self.environments:
      tmp = env.check(duplDomains, duplPorts, duplNames, names)
      if len(tmp) > 0 :
        errors[env.Name] = tmp
    return errors

  def findEnvironments(self, names, readyOnly = True):
    envs = []
    for env in self.environments:
      if (
        env.owner 
        and (env.ready or readyOnly == False)
        and (len(names) == 0 or names.count(env.Name) > 0) 
      ) :
        envs.append(env)
    return envs

  def clean(self, names, verbose):
    subprocess.call(['sudo', '-u', 'root', 'docker-clean', self.name])
    for env in self.findEnvironments(names):
      env.buildImage(verbose)
      env.runContainer(verbose)
      env.runHooks(verbose)


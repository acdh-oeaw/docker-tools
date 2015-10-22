class Configuration:
  accounts = None

  def __init__(self):
    self.accounts = []

    for accName in sorted(os.listdir('/home')):
      account = Account(accName)
      account.readConfig()
      self.accounts.append(account)

  def check(self):
    envs = self.findEnvironments([], [], False)
    domains = [i for sublist in [env.getDomains() for env in envs] for i in sublist]
    ports = [i for sublist in [env.getPorts() for env in envs] for i in sublist]
    names = [env.getName() for env in envs]

    duplDomains = [domain for domain, count in collections.Counter(domains).iteritems() if count > 1]
    duplPorts = [port for port, count in collections.Counter(ports).iteritems() if count > 1]
    duplNames = [name for name, count in collections.Counter(names).iteritems() if count > 1]

    for account in self.accounts:
      errors = account.check(duplDomains, duplPorts, duplNames, names)
      if len(errors) > 0 :
        print '  ' + account.name, ': ', errors
        noErrors = False

  def buildImages(self, projects, names, verbose):
    for env in self.findEnvironments(projects, names):
      try:
        env.buildImage(verbose)
      except Exception as e:
        print e

  def runContainers(self, projects, names, verbose):
    for env in self.findEnvironments(projects, names):
      try:
        env.runContainer(verbose)
      except Exception as e:
        print e

  def runHooks(self, projects, names, verbose):
    for env in self.findEnvironments(projects, names):
      try:
        env.runHooks(verbose)
      except Exception as e:
        print e

  def runConsole(self, projects, name, action):
    envs = self.findEnvironments(projects, [name])
    if len(envs) == 1 :
      try:
        if action == 'enter' :
          root = False
        elif action == 'enter-as-root' :
          root = True
        else :
          raise Exception('Unsupported action')
        return envs[0].runConsole(root)
      except Exception as e:
        print '  ' + str(e)
        return
    print "  Given environment not found or not ready"

  def showLogs(self, projects, name):
    envs = self.findEnvironments(projects, [name])
    if len(envs) == 1 :
      return envs[0].showLogs()
    print "  Given environment not found or not ready"

  def clean(self, users, names, verbose):
    for account in self.accounts:
      if len(users) == 0 or users.count(account.name) > 0 :
        account.clean(names, verbose)

  def findEnvironments(self, projects, names, readyOnly = True):
    envs = []
    for account in self.accounts:
      if len(projects) == 0 or projects.count(account.name) > 0 :
        envs += account.findEnvironments(names, readyOnly)
    return envs

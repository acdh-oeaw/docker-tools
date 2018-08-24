import collections
import copy
import json
import os

from .Account import Account
from .Environments.Environment import Environment

class Configuration:
  cfg = None
  accounts = None
  cfgFile = '/etc/docker-tools.json'

  def __init__(self):
    self.accounts = []

    # initialize config
    Configuration.cfg = {
      'baseDir': '/home',
      'DockerImgBase': '/var/lib/docker/images',
      'DockerMntBase': '/srv/docker',
      'default': {},
      'projects': {}
    }
    if os.path.exists(Configuration.cfgFile):
      with open(Configuration.cfgFile, 'r') as cfgHandle:
        cfg = json.loads(cfgHandle.read())
      self.cfg.update(cfg)

    Environment.DockerImgBase = self.cfg['DockerImgBase']

    # initialize Account objects
    base = self.cfg['baseDir']
    for accName in sorted(os.listdir(base)):
      if os.path.isdir(os.path.join(base, accName)) :
        try:
          cfg = {'default': copy.deepcopy(self.cfg['default']), 'environments': {}}
          if accName in self.cfg['projects']:
            if 'default' in self.cfg['projects'][accName]:
              cfg['default'].update(self.cfg['projects'][accName]['default'])
            if 'environments' in self.cfg['projects'][accName]:
              cfg['environments'] = self.cfg['projects'][accName]['environments']
          
          account = Account(accName, cfg)
          account.readConfig()
          self.accounts.append(account)
        except Exception as e:
          pass 

  def check(self):
    envs = self.findEnvironments([], [], False)
    domains = [i for sublist in [env.getDomains() for env in envs] for i in sublist]
    ports = [i for sublist in [env.getPorts() for env in envs] for i in sublist]
    names = [env.getName() for env in envs]

    duplDomains = [domain for domain, count in collections.Counter(domains).iteritems() if count > 1]
    duplPorts = [port for port, count in collections.Counter(ports).iteritems() if count > 1]
    duplNames = [name for name, count in collections.Counter(names).iteritems() if count > 1]

    accountNames = []
    for account in self.accounts:
      accountNames.append(account.name)
      errors = account.check(duplDomains, duplPorts, duplNames, names)
      if len(errors) > 0 :
        print '  ' + account.name, ': ', errors
    accountNames.sort()
    if len(accountNames) > 1:
      for i in xrange(1, len(accountNames)):
        if accountNames[i].startswith(accountNames[i - 1]):
          print '  FATAL ERROR: nested project names %s and %s' % (accountNames[i - 1], accountNames[i])
          return False

  def stop(self, projects, names, verbose):
    for env in self.findEnvironments(projects, names):
      try:
        env.stop(True)
      except Exception as e:
        print '    ' + str(e)

  def clean(self, verbose):
    for account in self.accounts:
      if account.owner:
        account.clean(verbose)

  def buildImages(self, projects, names, verbose):
    for env in self.findEnvironments(projects, names):
      try:
        env.buildImage(verbose)
      except Exception as e:
        print '    ' + str(e)

  def runContainers(self, projects, names, verbose):
    n = 0
    for env in self.findEnvironments(projects, names):
      try:
        env.runContainer(verbose)
        n += 1
      except Exception as e:
        print '    ' + str(e)
    return n

  def runHooks(self, projects, names, verbose):
    for env in self.findEnvironments(projects, names):
      try:
        env.runHooks(verbose)
        env.runUserHooks(verbose)
      except Exception as e:
        print '    ' + str(e)

  def runCommand(self, projects, name, action, command):
    envs = self.findEnvironments(projects, [name])
    if len(envs) == 1 :
      try:
        if action == 'enter' :
          root = False
        elif action == 'enter-as-root' :
          root = True
        else :
          raise Exception('Unsupported action')
        return envs[0].runCommand(root, command)
      except Exception as e:
        print '  ' + str(e)
        return
    print "  Given environment not found or not ready"

  def showLogs(self, projects, name):
    envs = self.findEnvironments(projects, [name])
    if len(envs) == 1 :
      return envs[0].showLogs()
    print "  Given environment not found or not ready"

  def findEnvironments(self, projects, names, readyOnly = True):
    envs = []
    accountMatched = False
    for account in self.accounts:
      if len(projects) == 0 or projects.count(account.name) > 0 :
        envs += account.findEnvironments(names, readyOnly)
      if account.name in projects:
        accountMatched = True
    if len(envs) == 0:
      if len(projects) > 0 and not accountMatched:
        print '\nNO SUCH PROJECT - check -p parameter value\n'
      elif len(names) > 0:
        print '\nNO SUCH ENVIRONMENT - check -e parameter value\n'
    return envs


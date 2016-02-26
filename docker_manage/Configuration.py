import collections
import os

from .Account import Account

class Configuration:
  accounts = None

  def __init__(self):
    self.accounts = []

    base = '/home'
    for accName in sorted(os.listdir(base)):
      if os.path.isdir(os.path.join(base, accName)) :
        try:
          account = Account(accName)
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

    for account in self.accounts:
      errors = account.check(duplDomains, duplPorts, duplNames, names)
      if len(errors) > 0 :
        print '  ' + account.name, ': ', errors
        noErrors = False

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
    for account in self.accounts:
      if len(projects) == 0 or projects.count(account.name) > 0 :
        envs += account.findEnvironments(names, readyOnly)
    return envs

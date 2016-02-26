import os
import json
import subprocess
from docker import Client

from .Environments import *

class Account:
  base         = ''
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
    self.base = os.path.expanduser('~' + name)
    if not Param.isValidDir(self.base) :
      raise Exception('account does not exist')
    self.uid = os.stat(self.base).st_uid
    self.gid = os.stat(self.base).st_gid

    self.owner = os.access(self.base, os.W_OK)
  
  def readConfig(self):
    print '  ' + self.name
    confFileName = self.base + '/config.json'
    if os.path.isfile(confFileName):
      try:
        config = json.load(open(confFileName, 'r'))
        self.processConfig(config)
      except Exception as e:
        print '    Configuration file ' + confFileName + ' is not a valid JSON: ' + str(e)

  def processConfig(self, conf):
    if not isinstance(conf, list) :
      raise Exception('configuration is not a list')

    self.environments = []
    for envConf in conf:
      try:
        envConf['BaseDir'] = self.base
        envConf['UID']     = self.uid
        envConf['GID']     = self.gid
        envConf['Account'] = self.name
        if 'Type' in envConf :
          envName = 'Environment' + envConf['Type']
          for envType in IEnvironment.__subclasses__():
            if envName == envType.__name__:
              env = envType(envConf, self.owner)
              break
          else :
            raise Exception('environment is of unsupported type (' + envConf['Type'] + ')')
        else :
          raise Exception('environment has no type')
        self.environments.append(env)
      except Exception as e:
        print '    Error in ', (1 + len(self.environments)), ' environment: ', e

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

  def clean(self, verbose):
    # search for environments in systemd and apache config as well as in all docker containers
    envs = []
    for root, dirs, files in os.walk('/etc/systemd/system'):
      envs.extend([x[7:-8] for x in files if x.startswith('docker-%s-' % self.name)])
    for root, dirs, files in os.walk('/etc/httpd/conf.d/sites-enabled'):
      envs.extend([x[:-5] for x in files if x.startswith('%s-' % self.name)])
    cli = Client(base_url = 'unix://var/run/docker.sock')
    envs.extend([y[1:] for x in cli.containers(all = True) for y in x['Names'] if y.startswith('/%s-' % self.name)])

    toBeRemoved = set(envs) - set([e.Name for e in self.environments])
    if len(toBeRemoved) > 0 and verbose:
      print '  %s' % self.name
    for i in toBeRemoved:
      call = subprocess.Popen(['sudo', '-u', 'root', 'docker-clean', i], stdout = subprocess.PIPE, stderr=subprocess.PIPE)
      (out, err) = call.communicate()
      if verbose or err != '':
        print '    %s' % i
        print '\n'.join(['      %s' % x for x in out.split('\n')])
        print '\n'.join(['      %s' % x for x in err.split('\n')])

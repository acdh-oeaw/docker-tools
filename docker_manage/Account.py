import copy
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
  adminCfg     = None

  def __init__(self, name, adminCfg):
    self.environments = []
    self.adminCfg = adminCfg

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
    if self.owner:
        print('  ' + self.name)
    confFileName = self.base + '/config.json'
    if os.path.isfile(confFileName):
      try:
        config = json.load(open(confFileName, 'r'))
        self.processConfig(config)
      except Exception as e:
        if self.owner:
            print('    Configuration file ' + confFileName + ' is not a valid JSON: ' + str(e))

  def processConfig(self, conf):
    if not isinstance(conf, list) :
      raise Exception('configuration is not a list')

    self.environments = []
    for envConf in conf:
      try:
        envConf['BaseDir']     = self.base
        envConf['UID']         = self.uid
        envConf['GID']         = self.gid
        envConf['Account']     = self.name
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

        adminCfg = copy.deepcopy(self.adminCfg['default'])
        if envConf['Name'] in self.adminCfg['environments']:
          adminCfg.update(self.adminCfg['environments'][envConf['Name']])
        env.adminCfg = adminCfg
      except Exception as e:
        if self.owner:
          print '    Error in environment ', (1 + len(self.environments)), ': ', e

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = {}
    for env in self.environments:
      tmp = env.check(duplDomains, duplPorts, duplNames, names)
      if len(tmp) > 0 :
        errors[env.Name] = tmp
    return errors

  def findEnvironments(self, names, readOnly = True):
    envs = []
    for env in self.environments:
      if (
        env.owner 
        and (env.ready or readOnly == False)
        and (len(names) == 0 or names.count(env.Name) > 0) 
      ) :
        envs.append(env)
    return envs

  def clean(self, verbose):
    # search for environments in systemd and apache config as well as in all docker containers
    envsSystemd = []
    for root, dirs, files in os.walk('/etc/systemd/system'):
      envsSystemd.extend([x[7:-8] for x in files if x.startswith('docker-%s-' % self.name)])

    envsApache  = []
    for root, dirs, files in os.walk('/etc/httpd/conf.d/sites-enabled'):
      envsApache.extend([x[:-5] for x in files if x.startswith('%s-' % self.name)])

    cli = Client(base_url = 'unix://var/run/docker.sock')
    envsDocker = []
    for c in cli.containers(all = True):
      e = [x[1:] for x in c['Names'] if x.startswith('/%s-' % self.name) and Param.isValidName(x[(2 + len(self.name)):])]
      if len(e) == 1:
        envsDocker.extend(e)

    envs = []
    envs.extend(envsSystemd)
    envs.extend(envsApache)
    envs.extend(envsDocker)
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


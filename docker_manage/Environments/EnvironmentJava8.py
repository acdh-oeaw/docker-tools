import os

from . import *

class EnvironmentJava8(EnvironmentHTTP, IEnvironment):
  JavaParams    = None
  JavaUser      = 'user'
  JavaDir       = '/opt'
  CustomStartup = False

  def __init__(self, conf, owner):
    JavaParams = []

    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'java8'
    super(EnvironmentJava8, self).__init__(conf, owner)

    if 'CustomStartup' in conf and self.owner:
      if (
        not Param.isValidBoolean(conf['CustomStartup'])
        or (conf['CustomStartup'] == 'true' and not Param.isValidFile(self.BaseDir + '/' + conf['DockerfileDir'] + '/Dockerfile'))
      ):
        raise Exception('CustomStartup is not a string or has value other then true/false or a custom Dockerfile is not set')
      self.CustomStartup = conf['CustomStartup'] == 'true'

    if not self.CustomStartup:
      if not 'JavaParams' in conf or not Param.isValidParamsList(conf['JavaParams']) :
        raise Exception('JavaParams is missing or invalid')
      self.JavaParams = conf['JavaParams']

    if 'JavaUser' in conf :
      self.JavaUser = conf['JavaUser']

    if 'JavaDir' in conf :
      if not Param.isValidAbsPath(conf['JavaDir']) :
        raise Exception('JavaDir is not a valid absolute path')
      self.JavaDir = conf['JavaDir']

  def runHooks(self, verbose):
    super(EnvironmentJava8, self).runHooks(verbose)

    if verbose :
      if self.CustomStartup:
        print '    Custom startup method is provided via custom Dockerfile'
      else:
        print '    Setting up supervisord config'
    if not self.CustomStartup:
      confPath = '/tmp/' + self.Name
      with open(confPath, 'w') as config:
        config.write(self.supervisorConfigTemplate.format(
          Params = ' '.join(self.JavaParams),
          Dir    = self.JavaDir,
          User   = self.JavaUser
        ))
      self.runProcess(['docker', 'cp', confPath, self.Name+':/etc/supervisor/conf.d/supervisord.conf'], verbose, '', 'Copying supervisor config file failed')
      self.runProcess(['docker', 'exec', self.Name, 'supervisorctl', 'update'], verbose, '', 'Reloading supervisor config failed')
      os.remove(confPath)

  supervisorConfigTemplate = """
[supervisord]
nodaemon=true

[program:java]
command=/usr/bin/java {Params}
directory={Dir}
user={User}
"""

import os
import shutil
import subprocess
import re

from .IEnvironment import IEnvironment
from ..Param import Param
from ..HTTPReverseProxy import HTTPReverseProxy

class EnvironmentGeneric(IEnvironment, object):
  DockerImgBase = '/var/lib/docker/images'
  DockerMntBase = '/srv/docker'

  ready         = False
  owner         = False
  Name          = None
  UID           = None
  GID           = None
  UserName      = ''
  BaseDir       = None
  DockerfileDir = None
  Mounts        = None
  Links         = None
  Ports         = None
  Hosts         = None
  EnvVars       = None
  runAsUser     = False

  def __init__(self, conf, owner):
    self.Mounts  = []
    self.Links   = []
    self.Ports   = []
    self.Hosts   = []
    self.EnvVars = {}
    self.owner   = owner

    if not isinstance(conf, dict) :
      raise Exception('configuration is of a wrong type')

    if not 'Account' in conf or not Param.isValidName(conf['Account']) :
      raise Exception('Account name is missing or invalid')
    if not 'Name' in conf or not Param.isValidName(conf['Name']) :
      raise Exception('Name is missing or invalid')
    self.Name = conf['Account'] + '-' + conf['Name']

    if not 'BaseDir' in conf or not Param.isValidDir(conf['BaseDir']) :
      raise Exception('Base dir is missing or invalid')
    self.BaseDir = conf['BaseDir']

    if not 'UID' in conf or not Param.isValidNumber(conf['UID']) :
      raise Exception('UID is missing or invalid')
    self.UID = conf['UID']

    if not 'GID' in conf or not Param.isValidNumber(conf['GID']) :
      raise Exception('GID is missing or invalid')
    self.GID = conf['GID']

    if 'UserName' in conf :
      if not isinstance(conf['UserName'], basestring) :
        raise Exception('UserName is not a string')
      self.UserName = conf['UserName']

    if 'runAsUser' in conf:
      if not isinstance(conf['runAsUser'], basestring) or not ['true', 'false'].count(conf['runAsUser']) > 0 :
        raise Exception('runAsUser is not a string or has value other then true/false')
      self.runAsUser = conf['runAsUser'] == 'true'

    if (
      not 'DockerfileDir' in conf
      or not isinstance(conf['DockerfileDir'], basestring) 
      or self.owner and (
        not Param.isValidRelPath(conf['DockerfileDir'])
        or not (
          Param.isValidFile(self.BaseDir + '/' + conf['DockerfileDir'] + '/Dockerfile') 
          or Param.isValidFile(self.DockerImgBase + '/' + conf['DockerfileDir'] + '/Dockerfile')
        )
      )
    ) :
      raise Exception('DockerfileDir is missing or invalid')
    self.DockerfileDir = conf['DockerfileDir']

    if 'Mounts' in conf and self.owner:
      self.processMounts(conf['Mounts'])

    if 'Links' in conf and self.owner:
      self.processLinks(conf['Links'])

    if 'Ports' in conf :
      self.processPorts(conf['Ports'])

    if 'Hosts' in conf :
      self.processHosts(conf['Hosts'])

    if 'EnvVars' in conf :
      self.processEnvVars(conf['EnvVars'])

  def processMounts(self, conf):
    if not isinstance(conf, list):
      conf = [conf]

    for mount in conf:
      if not isinstance(mount, dict) :
        raise Exception(str(len(self.mounts) + 1) + ' mount point description is not a dictionary')
      if (
        not 'Host' in mount  
        or not (Param.isValidRelPath(mount['Host']) or Param.isValidAbsPath(mount['Host']))
        or not (Param.isValidDir(self.BaseDir + '/' + mount['Host']) or Param.isValidFile(self.BaseDir + '/' + mount['Host']))
      ) :
        raise Exception(str(len(self.Mounts) + 1) + ' mount point host mount point is missing or invalid')
      if not 'Guest' in mount :
        raise Exception(str(len(self.Mounts) + 1) + ' mount point guest mount point is missing')
      if not 'Rights' in mount or (mount['Rights'] != 'ro' and mount['Rights'] != 'rw') :
        raise Exception(str(len(self.Mounts) + 1) + ' mount point access rights are missing or invalid')
      self.Mounts.append(mount)

  def processLinks(self, conf):
    if not isinstance(conf, list) :
      conf = [conf]

    for link in conf :
      if not isinstance(link, dict) :
        raise Exception(str(len(self.Links) + 1) + ' link definition is not a dictionary')
      if not 'Name' in link or not isinstance(link['Name'], basestring) :
        raise Exception(str(len(self.Links) + 1) + ' link container name is missing or invalid')
      if not 'Alias' in link or not isinstance(link['Alias'], basestring) :
        raise Exception(str(len(self.Links) + 1) + ' link alias is missing or invalid')
      self.Links.append(link)

  def processPorts(self, conf):
    if not isinstance(conf, list) :
      conf = [conf]

    for port in conf:
      if not isinstance(port, dict) :
        raise Exception(str(len(self.Ports) + 1) + ' port forwarding description is not a dictionary')

      if not 'Type' in port or not port['Type'] in ['HTTP', 'tunnel'] :
        raise Exception(str(len(self.Ports) + 1) + ' port forwarding type is missing or invalid')

      if not 'Host' in port or not Param.isValidNumber(port['Host']) or int(port['Host']) < 1000 or int(port['Host']) > 65535 :
        if 'Host' in port and port['Type'] == 'HTTP' and int(port['Host']) == 0 :
          port['Host'] = HTTPReverseProxy.getPort()
        else :
          raise Exception (str(len(self.Ports) + 1) + ' port forwarding host port is missing or invalid')

      if not 'Guest' in port or not Param.isValidNumber(port['Guest']) or int(port['Guest']) < 1 or int(port['Guest']) > 65535 :
        raise Exception(str(len(self.Ports) + 1) + ' port forwarding guest port is missing or invalid')

      if port['Type'] == 'HTTP' :
        if not 'ws' in port :
          port['ws'] = []
        if not isinstance(port['ws'], list) :
          port['ws'] = [ port['ws'] ]
        for ws in port['ws']:
          if not isinstance(ws, basestring) or not Param.isValidAlias(ws) :
            raise Exception(str(len(self.Ports) + 1) + ' port forwarding websockets paths are invalid')

        if not 'Alias' in port :
          port['Alias'] = ''
        elif not Param.isValidAlias(port['Alias']) :
          raise Exception(str(len(self.Ports) + 1) + ' port alias is invalid')
        port['Alias'] = re.sub('/$', '', re.sub('^/', '', port['Alias']))
        port['Alias'] += '/' if port['Alias'] != '' else ''

      self.Ports.append(port)

  def processHosts(self, conf):
    if not isinstance(conf, list) :
      conf = [conf]

    for host in conf:
      if not isinstance(host, dict) :
        raise Exception(str(len(self.Hosts) + 1) + ' host name definition is not a directory')
      if not 'Name' in host or not Param.isValidHostName(host['Name']) :
        raise Exception(str(len(self.Hosts) + 1) + ' host name definition - host name is missing or invalid ')
      if not 'IP' in host or not Param.isValidIP(host['IP']) :
        raise Exception(str(len(self.Hosts) + 1) + ' host name definition - IP number is missing or invalid ')
      self.Hosts.append(host)

  def processEnvVars(self, conf):
    if not isinstance(conf, dict) :
      raise Exception('Environment variables definition is not a dictionary')

    for name, value in conf.iteritems():
      if not Param.isValidVarName(name) :
        raise Exception(str(len(self.EnvVars) + 1) + ' environment variable name is invalid')
      if not isinstance(value, basestring) :
        raise Exception(str(len(self.EnvVars) + 1) + ' environment variable value is not a string')
      self.EnvVars[name] = value

  def check(self, duplDomains, duplPorts, duplNames, names):
    errors = []
    if self.Name in duplNames :
      errors.append('Duplicated name: ' + self.Name)
    for port in self.Ports:
      if port['Host'] in duplPorts :
        errors.append('Port ' + str(port) + ' is duplicated')
    for link in self.Links:
      if not link['Name'] in names :
        errors.append('Alias container ' + link['Name'] + ' does not exist')
    if len(errors) == 0 :
      self.ready = True
    return errors

  def buildImage(self, verbose):
    if not self.owner :
      raise Exception('Must be environment owner to build an image')
    if not self.ready :
      raise Exception('Environment is not ready - it was not checked or there were errord during check')

    # prepare place for a final dockerfileDir
    tmpDir = self.DockerImgBase + '/tmp/' + self.Name
    shutil.rmtree(tmpDir, True)

    # check dockerfile
    if Param.isValidFile(self.BaseDir + '/' + self.DockerfileDir + '/Dockerfile') :
      dockerfileDir = self.BaseDir + '/' + self.DockerfileDir
      # make a copy of the dockerfileDir and inject data to the Dockerfile
      shutil.copytree(dockerfileDir, tmpDir)
    elif Param.isValidFile(self.DockerImgBase + '/' + self.DockerfileDir + '/Dockerfile') : 
      dockerfileDir = self.DockerImgBase + '/' + self.DockerfileDir
      # create a simple Dockerfile based on provided one
      os.mkdir(tmpDir)
      with open(tmpDir + '/Dockerfile', 'w') as dockerfile:
        dockerfile.write('FROM acdh/' + self.DockerfileDir + '\n')
        dockerfile.write('MAINTAINER acdh-tech <acdh-tech@oeaw.ac.at>\n')
    else :
      self.ready = False
      raise Exception('There is no Dockerfile ' + self.DockerfileDir + ' ' + self.BaseDir)

    print '  ' + self.Name

    self.injectUserEnv(tmpDir + '/Dockerfile')
    self.runProcess(['docker', 'build', '--force-rm=true', '-t', 'acdh/' + self.Name, tmpDir], verbose, '', 'Build failed')
    shutil.rmtree(tmpDir)

  def runContainer(self, verbose):
    if not self.owner :
      raise Exception('Must be environment owner to run a container')
    if not self.ready :
      raise Exception('Environment is not ready - it was not checked or there were errord during check/build')

    print '  ' + self.Name
    # remove
    self.runProcess(['docker', 'rm', '-f', '-v', self.Name], verbose, '    Removing old container...', None)
    # run
    self.runProcess(['docker', 'run', '--name', self.Name] + self.getDockerOpts() + ['acdh/' + self.Name], verbose, '    Creating container...', 'Container creation failed')
    # mount exported volumes
    self.runProcess(['sudo', '-u', 'root', 'docker-mount-volumes', '-v', '-c', self.Name], verbose, '    Mounting docker volumes', 'Volume mounting failed')
    # create systemd script
    self.runProcess(['sudo', '-u', 'root', 'docker-register-systemd', self.Name], verbose, '    Registering in systemd', 'Systemd script creation failed')

  def runHooks(self, verbose):
    if not self.owner :
      raise Exception('Must be environment owner to run hooks')

    print '  ' + self.Name

  def runCommand(self, root, command = None):
    if not self.ready :
      return False
    if command is None or not isinstance(command, list) or len(command) == 0:
      command = ['/bin/bash']

    args = ['docker', 'exec', '-ti', '-u', 'root', self.Name] + command
    if not root :
      args[4] = 'user'
    subprocess.call(args)

  def showLogs(self):
    if not self.ready :
      raise Exception('Environment is not ready - it was not checked or there were errord during check')

    subprocess.call(['docker', 'logs', self.Name])

  def runProcess(self, args, verbose, header, errorMsg):
    proc = None
    if verbose :
      print header
      ret = subprocess.call(args)
    else :
      proc = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
      out, err = proc.communicate()
      ret = proc.returncode

    if ret != 0 and not errorMsg is None:
      self.ready = False
      if not proc is None:
        print out + '\n' + err
      raise Exception(errorMsg)
    return ret

  def injectUserEnv(self, dockerfilePath):
    if self.UserName != '' :
      # adjusting existing guest user to meet UID and GID used in host
      cmd =  'sed -i -r -e "s/^' + self.UserName + ':x:[0-9]+:[0-9]+:/' + self.UserName + ':x:' + str(self.UID) + ':' + str(self.GID) + ':/" /etc/passwd;'
      cmd += 'sed -i -r -e "s/^' + self.UserName + ':x:[0-9]+:/' + self.UserName + ':x:' + str(self.GID) + ':/" /etc/group;'
    else :
      # adding generic system user and group for UID and GID used in host
      cmd =  'echo "user:x:' + str(self.UID) + ':' + str(self.GID) + '::' + self.getGuestHomeDir() + ':/bin/bash" >> /etc/passwd;'
      cmd += 'echo "user:x:' + str(self.GID) + ':" >> /etc/group;'
      cmd += 'echo "user:*:16231:0:99999:7:::" >> /etc/shadow;'
    cmd = 'RUN ' + cmd + '\n'

    for name, value in self.EnvVars.iteritems():
      cmd += 'ENV ' + name + ' ' + value + '\n'

    with open(dockerfilePath, 'r') as dockerfile:
      commands = dockerfile.read()
      commands = re.sub('\\n(MAINTAINER[^\\n]*)', '\n\\1\n' + cmd, commands) 
    with open(dockerfilePath, 'w') as dockerfile:
      dockerfile.write(commands)
    if self.runAsUser:
      with open(dockerfilePath, 'a') as dockerfile:
        dockerfile.write('\nUSER user\n')

  def getName(self):
    return self.Name

  def getPorts(self):
    ports = []
    for port in self.Ports:
      ports.append(port['Host'])
    return ports

  def getDomains(self):
    return []

  def getDockerOpts(self):
    dockerOpts = ['-d']
    for mount in self.Mounts:
      dockerOpts += ['-v',  self.BaseDir + '/' + mount['Host'] + ':' + mount['Guest'] + ':' + mount['Rights']]
    for port in self.Ports:
      dockerOpts += ['-p', str(port['Host']) + ':' + str(port['Guest'])]
    for link in self.Links:
      dockerOpts += ['--link', link['Name'] + ':' + link['Alias']]
    for host in self.Hosts:
      dockerOpts += ['--add-host', host['Name'] + ':' + host['IP']]
    return dockerOpts

  def getGuestHomeDir(self):
    return '/'


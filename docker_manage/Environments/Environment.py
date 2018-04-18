import os
import shutil
import subprocess
import re
import random
import codecs
import docker
from docker import Client

from . import *


class Environment(IEnvironment, object):
    DockerImgBase = None

    ready = False
    owner = False
    Name = None
    ID = None
    UID = None
    GID = None
    UserName = ''
    GroupName = None
    BaseDir = None
    DockerfileDir = None
    Mounts = None
    Links = None
    Networks = None
    Ports = None
    Hosts = None
    EnvVars = None
    Version = None
    BackupDir = None
    runAsUser = False
    LogDir = None
    LogDirMount = None
    userHookUser = None
    userHookRoot = None
    adminCfg = None

    def __init__(self, conf, owner):
        self.Mounts = []
        self.Links = []
        self.Networks = []
        self.Ports = []
        self.Hosts = []
        self.EnvVars = {}
        self.owner = owner
        self.adminCfg = {}
        self.volumesToCopy = []

        if not isinstance(conf, dict):
            raise Exception('configuration is of a wrong type')

        if not 'Account' in conf or not Param.isValidName(conf['Account']):
            raise Exception('Account name is missing or invalid')
        if not 'Name' in conf or not Param.isValidName(conf['Name']):
            raise Exception('Name is missing or invalid')
        self.Name = conf['Account'] + '-' + conf['Name']
        if not 'ID' in conf or not Param.isValidNumber(conf['ID']):
            if self.owner:
                print('    Warning! Redmine issue ID is missing in environment %s' % self.Name)
        else:
            self.ID = conf['ID']

        if not 'BaseDir' in conf or not Param.isValidDir(conf['BaseDir']):
            raise Exception('Base dir is missing or invalid')
        self.BaseDir = conf['BaseDir']

        if not 'UID' in conf or not Param.isValidNumber(conf['UID']):
            raise Exception('UID is missing or invalid')
        self.UID = conf['UID']

        if not 'GID' in conf or not Param.isValidNumber(conf['GID']):
            raise Exception('GID is missing or invalid')
        self.GID = conf['GID']

        if 'UserName' in conf:
            if not isinstance(conf['UserName'], basestring):
                raise Exception('UserName is not a string')
            self.UserName = conf['UserName']

        if 'GroupName' in conf:
            if not isinstance(conf['GroupName'], basestring):
                raise Exception('GroupName is not a string')
            self.GroupName = conf['GroupName']

        if 'runAsUser' in conf:
            if not Param.isValidBoolean(conf['runAsUser']):
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
        ):
            raise Exception('DockerfileDir ' + conf['DockerfileDir'] + ' is missing or invalid')
        self.DockerfileDir = conf['DockerfileDir']

        if 'Mounts' in conf and self.owner:
            self.processMounts(conf['Mounts'])

        if 'Links' in conf and self.owner:
            self.processLinks(conf['Links'])

        if 'Networks' in conf and self.owner:
            self.processNetworks(conf['Networks'], conf['Account'])

        if 'Ports' in conf:
            self.processPorts(conf['Ports'])

        if 'Hosts' in conf:
            self.processHosts(conf['Hosts'])

        if 'EnvVars' in conf:
            self.processEnvVars(conf['EnvVars'])

        if 'Version' in conf:
            if not isinstance(conf['Version'], basestring):
                raise Exception('Version is not a string')
            self.Version = conf['Version']

        if 'BackupDir' in conf:
            if not Param.isValidDir(self.BaseDir + '/' + conf['BackupDir']):
                raise Exception('BackupDir is invalid')
            self.BackupDir = conf['BackupDir']

        if 'Hooks' in conf and self.owner:
            self.processUserHooks(conf['Hooks'])

    def processUserHooks(self, conf):
        if not isinstance(conf, dict):
            raise Exception('Invalid RunHooks')
        
        if 'User' in conf:
            if not Param.isValidFile(self.BaseDir + '/' + conf['User']) or not Param.isValidRelPath(conf['User']):
                raise Exception('User RunHook is not a file')
            self.userHookUser = self.BaseDir + '/' + conf['User']

        if 'Root' in conf:
            if not Param.isValidFile(self.BaseDir + '/' + conf['Root']) or not Param.isValidRelPath(conf['Root']):
                raise Exception('Root RunHook is not a file')
            self.userHookRoot = self.BaseDir + '/' + conf['Root']      

    def processLogDir(self, conf, enforce = False):
        if 'LogDir' in conf:
            if (
                self.owner and (
                    not Param.isValidRelPath(conf['LogDir'])
                    or not Param.isValidDir(self.BaseDir + '/' + conf['LogDir'])
                )
            ):
                raise Exception('LogDir is invalid')
            self.LogDir = conf['LogDir']
            if self.LogDirMount is not None:
                self.Mounts.append({"Host": self.LogDir, "Guest": self.LogDirMount, "Rights": "rw"})
        else:
            if enforce:
                raise Exception('LogDir is not specified')
            elif self.owner:
                print('    Warning! LogDir is not specified in environment %s' % self.Name) 

    def processMounts(self, conf):
        if not isinstance(conf, list):
            conf = [conf]

        for mount in conf:
            if not isinstance(mount, dict):
                raise Exception(str(len(self.mounts) + 1) + ' mount point description is not a dictionary')
            if (
                            not 'Host' in mount
                        or not (Param.isValidRelPath(mount['Host']) or Param.isValidAbsPath(mount['Host']))
                    or not (Param.isValidDir(self.BaseDir + '/' + mount['Host']) or Param.isValidFile(
                                self.BaseDir + '/' + mount['Host']))
            ):
                raise Exception(str(len(self.Mounts) + 1) + ' mount point host mount point is missing or invalid')
            if not 'Guest' in mount:
                raise Exception(str(len(self.Mounts) + 1) + ' mount point guest mount point is missing')
            if not 'Rights' in mount or (mount['Rights'] != 'ro' and mount['Rights'] != 'rw'):
                raise Exception(str(len(self.Mounts) + 1) + ' mount point access rights are missing or invalid')
            self.Mounts.append(mount)

    def processLinks(self, conf):
        if not isinstance(conf, list):
            conf = [conf]

        for link in conf:
            if not isinstance(link, dict):
                raise Exception(str(len(self.Links) + 1) + ' link definition is not a dictionary')
            if not 'Name' in link or not isinstance(link['Name'], basestring):
                raise Exception(str(len(self.Links) + 1) + ' link container name is missing or invalid')
            if not 'Alias' in link or not isinstance(link['Alias'], basestring):
                raise Exception(str(len(self.Links) + 1) + ' link alias is missing or invalid')
            self.Links.append(link)

    def processNetworks(self, conf, account):
        if not isinstance(conf, list):
            conf = [conf]

        for network in conf:
            if isinstance(network, basestring):
                network = {'Name': network}
            if not isinstance(network, dict):
                raise Exception(str(len(self.Networks) + 1) + ' network name is not a dictionary')
            if 'Alias' in network and not isinstance(network['Alias'], basestring):
                raise Exception(str(len(self.Networks) + 1) + ' network alias is invalid')
            network['Name'] = account + '-' + network['Name']
            self.Networks.append(network)

    def processPorts(self, conf):
        if not isinstance(conf, list):
            conf = [conf]

        for port in conf:
            if not isinstance(port, dict):
                raise Exception(str(len(self.Ports) + 1) + ' port forwarding description is not a dictionary')

            if 'Type' not in port or port['Type'] not in ['HTTP', 'tunnel']:
                raise Exception(str(len(self.Ports) + 1) + ' port forwarding type is missing or invalid')

            if 'Host' not in port or not Param.isValidNumber(port['Host']) or int(port['Host']) < 1000 or int(
                    port['Host']) > 65535:
                if 'Host' in port and port['Type'] == 'HTTP' and int(port['Host']) == 0:
                    port['Host'] = HTTPReverseProxy.getPort()
                else:
                    raise Exception(str(len(self.Ports) + 1) + ' port forwarding host port is missing or invalid')

            if 'Guest' not in port or not Param.isValidNumber(port['Guest']) or int(port['Guest']) < 1 or int(
                    port['Guest']) > 65535:
                raise Exception(str(len(self.Ports) + 1) + ' port forwarding guest port is missing or invalid')

            if port['Type'] == 'HTTP':
                if not 'ws' in port:
                    port['ws'] = []
                if not isinstance(port['ws'], list):
                    port['ws'] = [port['ws']]
                for ws in port['ws']:
                    if not isinstance(ws, basestring) or not Param.isValidAlias(ws):
                        raise Exception(str(len(self.Ports) + 1) + ' port forwarding websockets paths are invalid')

                if not 'Alias' in port:
                    port['Alias'] = ''
                elif not Param.isValidAlias(port['Alias']):
                    raise Exception(str(len(self.Ports) + 1) + ' port alias is invalid')
                port['Alias'] = re.sub('/$', '', re.sub('^/', '', port['Alias']))
                port['Alias'] += '/' if port['Alias'] != '' else ''

            self.Ports.append(port)

    def processHosts(self, conf):
        if not isinstance(conf, list):
            conf = [conf]

        for host in conf:
            if not isinstance(host, dict):
                raise Exception(str(len(self.Hosts) + 1) + ' host name definition is not a directory')
            if not 'Name' in host or not Param.isValidHostName(host['Name']):
                raise Exception(str(len(self.Hosts) + 1) + ' host name definition - host name is missing or invalid ')
            if not 'IP' in host or not Param.isValidIP(host['IP']):
                raise Exception(str(len(self.Hosts) + 1) + ' host name definition - IP number is missing or invalid ')
            self.Hosts.append(host)

    def processEnvVars(self, conf):
        if not isinstance(conf, dict):
            raise Exception('Environment variables definition is not a dictionary')

        for name, value in conf.iteritems():
            if not Param.isValidVarName(name):
                raise Exception(str(len(self.EnvVars) + 1) + ' environment variable name is invalid')
            if not isinstance(value, basestring):
                raise Exception(str(len(self.EnvVars) + 1) + ' environment variable value is not a string')
            self.EnvVars[name] = value

    def check(self, duplDomains, duplPorts, duplNames, names):
        errors = []
        if self.Name in duplNames:
            errors.append('Duplicated name: ' + self.Name)
        for port in self.Ports:
            if port['Host'] in duplPorts:
                errors.append('Port ' + str(port) + ' is duplicated')
        for link in self.Links:
            if not link['Name'] in names:
                errors.append('Alias container ' + link['Name'] + ' does not exist')
        if len(errors) == 0:
            self.ready = True
        return errors

    def buildImage(self, verbose):
        if not self.owner:
            raise Exception('Must be environment owner to build an image')
        if not self.ready:
            raise Exception('Environment is not ready - it was not checked or there were errord during check')

        # prepare place for a final dockerfileDir
        tmpDir = self.DockerImgBase + '/tmp/' + self.Name
        shutil.rmtree(tmpDir, True)

        # check dockerfile
        if Param.isValidFile(self.BaseDir + '/' + self.DockerfileDir + '/Dockerfile'):
            dockerfileDir = self.BaseDir + '/' + self.DockerfileDir
        elif Param.isValidFile(self.DockerImgBase + '/' + self.DockerfileDir + '/Dockerfile'):
            dockerfileDir = self.DockerImgBase + '/' + self.DockerfileDir
        else:
            self.ready = False
            raise Exception('There is no Dockerfile ' + self.DockerfileDir + ' ' + self.BaseDir)
        # make a copy of the dockerfileDir and inject data to the Dockerfile
        shutil.copytree(dockerfileDir, tmpDir)

        print('  ' + self.Name)

        self.injectUserEnv(tmpDir + '/Dockerfile')
        self.adjustVersion(tmpDir + '/Dockerfile')
        self.runProcess(['docker', 'build', '--force-rm=true', '-t', 'acdh/' + self.Name, tmpDir], verbose, '',
                        'Build failed')
        shutil.rmtree(tmpDir)

    def checkVolumes(self, cli):
        volumesToCopy = []
        volumesToCopy.extend(self.volumesToCopy)
        volumes = cli.inspect_image('acdh/' + self.Name)['Config']['Volumes']
        if volumes is None:
            return volumesToCopy
        for vol, hostPath in volumes.iteritems():
            vol = '/' + re.sub('^/?(.*)/?$', '\\1', vol) + '/'
            matched = False
            for mount in self.Mounts:
                guest = '/' + re.sub('^/?(.*)/?$', '\\1', mount['Guest']) + '/'
                if guest == vol:
                    matched = True
                    if len(os.listdir(self.BaseDir + '/' + mount['Host'])) == 0:
                        volumesToCopy.append({'Host': mount['Host'], 'Volume': vol})
                    break
            if not matched:
                raise Exception('No mount point provided for path ' + vol)
        return volumesToCopy

    def checkNetworks(self):
        for network in self.Networks:
            out = subprocess.check_output(['docker', 'network', 'ls']).split('\n')
            out = [x for x in out if re.match('^[0-9a-f]+ +' + network['Name'], x)]
            if len(out) == 0:
                self.runProcess(['docker', 'network', 'create', '-d', 'bridge', network['Name']], False, '', 'Network creation failed')
            param = ['docker', 'network', 'connect', network['Name'], self.Name]
            if 'Alias' in network:
                param = param + ['--alias', network['Alias']]
            self.runProcess(param, False, '', 'Failed to connect to the network')

    def runContainer(self, verbose):
        if not self.owner:
            raise Exception('Must be environment owner to run a container')
        if not self.ready:
            raise Exception('Environment is not ready - it was not checked or there were error during check/build')

        print('  ' + self.Name)
        # remove
        try:
            self.stop(False)
        except Exception:
            pass
        self.runProcess(['docker', 'rm', '-f', '-v', self.Name], verbose, '    Removing old container...', None)
        # check and prepare volumes if necessary
        cli = Client(base_url='unix://var/run/docker.sock')
        volumesToCopy = self.checkVolumes(cli)
        if len(volumesToCopy) > 0:
            mountsTmp = self.Mounts
            self.Mounts = []
            self.runProcess(['docker', 'run', '--name', self.Name] + self.getDockerOpts() + ['acdh/' + self.Name],
                            verbose, '    Creating temporary container to copy volumes content...',
                            'Container creation failed')
            volumes = cli.inspect_container(self.Name)['Config']['Volumes']
            for item in self.volumesToCopy:
                volumes.update({item['Volume'][:-1]: {}})
            for v in volumesToCopy:
                for volume, hostPath in volumes.iteritems():
                    volume = '/' + re.sub('^/?(.*)/?$', '\\1', volume) + '/'
                    if volume == v['Volume']:
                        os.rmdir(self.BaseDir + '/' + v['Host'])
                        self.runProcess(['docker', 'cp', self.Name + ':' + volume, self.BaseDir + '/' + v['Host']],
                                        verbose, '    Copying ' + volume + ' into ' + v['Host'], 'Copying failed')
            self.runProcess(['docker', 'rm', '-f', '-v', self.Name], verbose, '    Removing temporary container...',
                            None)
            self.Mounts = mountsTmp
        # run
        self.runProcess(['docker', 'run', '--name', self.Name] + self.getDockerOpts() + ['acdh/' + self.Name], verbose,
                        '    Creating container...', 'Container creation failed')
        # check networks
        self.checkNetworks()
        # create systemd script & run systemctl to set right status of the service
        self.runProcess(['sudo', '-u', 'root', 'docker-register-systemd', self.Name], verbose,
                        '    Registering in systemd', 'Systemd script creation failed')
        self.runProcess(['sudo', '-u', 'root', 'docker-systemctl', 'start', self.Name], verbose,
                        '    Setting systemd service status', 'Setting systemd service status failed')

    def runHooks(self, verbose):
        if not self.owner:
            raise Exception('Must be environment owner to run hooks')

        print('  ' + self.Name)

    def runUserHooks(self, verbose):
        if not self.owner:
            raise Exception('Must be environment owner to run hooks')

        if not self.userHookRoot is None:
            self.runProcess(['docker', 'cp', self.userHookRoot, self.Name + ':/tmp/root.sh'], False, '', 'Copying user hook failed')
            self.runProcess(['docker', 'exec', '-u', 'root', self.Name, 'bash', '/tmp/root.sh'], verbose, '', 'Running user hook failed')

        if not self.userHookUser is None:
            self.runProcess(['docker', 'cp', self.userHookUser, self.Name + ':/tmp/user.sh'], False, '', 'Copying user hook failed')
            self.runProcess(['docker', 'exec', '-u', self.UserName, self.Name, 'bash', '/tmp/user.sh'], verbose, '', 'Running user hook failed')

    def runCommand(self, root, command=None):
        if not self.ready:
            return False
        opts = '-i'
        if command is None or not isinstance(command, list) or len(command) == 0:
            command = ['/bin/bash']
            opts += 't'

        args = ['docker', 'exec', opts, '-u', 'root', self.Name] + command
        if not root:
            args[4] = self.UserName if self.UserName != '' else 'user'
        subprocess.call(args)

    def showLogs(self):
        if not self.ready:
            raise Exception('Environment is not ready - it was not checked or there were errord during check')

        subprocess.call(['docker', 'logs', self.Name])

    def runProcess(self, args, verbose, header, errorMsg):
        proc = None
        if verbose:
            print(header)
            print(' '.join(args))
            ret = subprocess.call(args)
        else:
            proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            ret = proc.returncode

        if ret != 0 and not errorMsg is None:
            self.ready = False
            if not proc is None:
                print(out + '\n' + err)
            raise Exception(errorMsg)
        return ret

    def stop(self, verbose):
        if verbose:
            print('  ' + self.Name)

        ret = subprocess.call(['sudo', '-u', 'root', 'docker-systemctl', 'stop', self.Name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ret != 0:
            raise Exception('Failed to stop')

        if verbose:
            print '    stopped'

    def injectUserEnv(self, dockerfilePath):
        cmd = ''

        if self.GroupName is None:
           self.GroupName = self.UserName

        if self.GroupName != '':
            cmd += 'groupmod --gid ' + str(self.GID) + ' "' + self.GroupName + '" && '
        else:
            cmd += 'groupadd --gid ' + str(self.GID) + ' user && '

        if self.UserName != '':
            cmd += 'usermod --gid ' + str(self.GID) + ' --uid ' + str(self.UID) + ' "' + self.UserName + '" && '
        else:
            cmd += 'useradd --gid ' + str(self.GID) + ' --uid ' + str(self.UID) + ' -d ' + self.getGuestHomeDir() + ' user && '
            cmd += 'echo "user:$6$04SIq7OY$7PT2WujGKsr6013IByauNo0tYLj/fperYRMC4nrsbODc9z.cnxqXDRkAmh8anwDwKctRUTiGhuoeali4JoeW8/:16231:0:99999:7:::" >> /etc/shadow && '
        cmd = 'USER root\nRUN ' + cmd[:-3] + '\n'

        for name, value in self.EnvVars.iteritems():
            cmd += 'ENV ' + name + ' ' + value + '\n'

        with codecs.open(dockerfilePath, mode='r', encoding='utf-8') as dockerfile:
            commands = dockerfile.read()
        if re.search('\\n#@INJECT_USER@[^\\n]*', commands) is not None:
            commands = re.sub('\\n#(@INJECT_USER@[^\\n]*)', '\n' + cmd, commands)
        else:
            commands = re.sub('\\n(MAINTAINER[^\\n]*)', '\n\\1\n' + cmd, commands)
        with codecs.open(dockerfilePath, mode='w', encoding='utf-8') as dockerfile:
            dockerfile.write(commands)
        if self.runAsUser:
            with codecs.open(dockerfilePath, mode='a', encoding='utf-8') as dockerfile:
                dockerfile.write("\nUSER %(user)s\n" % {'user': self.UserName if self.UserName != '' else 'user'})

    def adjustVersion(self, dockerfile):
        pass

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
        dockerOpts = ['-d', '-h', self.Name]
        for mount in self.Mounts:
            dockerOpts += ['-v', self.BaseDir + '/' + mount['Host'] + ':' + mount['Guest'] + ':' + mount['Rights']]
        for port in self.Ports:
            dockerOpts += ['-p', str(port['Host']) + ':' + str(port['Guest'])]
        for link in self.Links:
            dockerOpts += ['--link', link['Name'] + ':' + link['Alias']]
        dockerOpts += ['--network', 'bridge']
        for host in self.Hosts:
            dockerOpts += ['--add-host', host['Name'] + ':' + host['IP']]
        for option, value in self.adminCfg.iteritems():
            if not isinstance(value, list):
                value = [value]
            for v in value:
                dockerOpts.append('--' + str(option))
                dockerOpts.append(str(v))
        return dockerOpts

    def getGuestHomeDir(self):
        return '/'


class EnvironmentGeneric(Environment, IEnvironment):
    pass

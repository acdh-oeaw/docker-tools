import codecs
import re
from . import *


class EnvironmentDrupal7(EnvironmentPHP, IEnvironment):
    skipDocumentRoot = True
    Version = '43'

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = 'http_drupal7'
        self.ImitateHTTPS = self.HTTPS

        super(EnvironmentDrupal7, self).__init__(conf, owner)

        if not 'SiteDir' in conf or not Param.isValidRelPath(conf['SiteDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['SiteDir']):
            raise Exception('SiteDir is missing or invalid')
        self.Mounts.append({"Host": conf['SiteDir'], "Guest": '/var/www/html/sites/default', "Rights": "rw"})

        if not 'AllDir' in conf or not Param.isValidRelPath(conf['AllDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['AllDir']):
            raise Exception('AllDir is missing or invalid')
        self.Mounts.append({"Host": conf['AllDir'], "Guest": '/var/www/html/sites/all', "Rights": "rw"})

    # as Drupal environment does not have DocumentRoot it is not clear what
    # should be a base dir for aliases
    def processAliases(self, conf):
        pass

    def runHooks(self, verbose):
        super(EnvironmentDrupal7, self).runHooks(verbose)

        if verbose:
            print('    Setting up drupal permissions')
        self.runProcess(
            ['docker', 'exec', self.Name, 'chown', '-R', self.UserName + ':' + self.UserName, '/var/www/html'], verbose,
            '', 'Setting up permissions failed')

    def adjustVersion(self, dockerfile):
        hashes = {
            '36': '98e1f62c11a5dc5f9481935eefc814c5',
            '37': '3a70696c87b786365f2c6c3aeb895d8a',
            '38': 'c18298c1a5aed32ddbdac605fdef7fce',
            '39': '6f42a7e9c7a1c2c4c9c2f20c81b8e79a',
            '40': 'd4509f13c23999a76e61ec4d5ccfaf26',
            '41': '7636e75e8be213455b4ac7911ce5801f',
            '42': '9a96f67474e209dd48750ba6fccc77db',
            '43': 'c6fb49bc88a6408a985afddac76b9f8b',
            '44': '965ab5fe5457625ec8c18e5c1c455008',
            '50': 'f23905b0248d76f0fc8316692cd64753'
        }

        if self.Version not in hashes:
            raise Exception('Version %s is not supported' % self.Version)

        with codecs.open(dockerfile, mode='r', encoding='utf-8') as df:
            commands = df.read()
            commands = re.sub('@VERSION@', '7.' + self.Version, commands)
            commands = re.sub('@HASH@', hashes[self.Version], commands)
        with codecs.open(dockerfile, mode='w', encoding='utf-8') as df:
            df.write(commands)


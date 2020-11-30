import codecs
import re
from . import *


class EnvironmentDrupal7(EnvironmentPHP, IEnvironment):
    skipDocumentRoot = True
    Version = '75'

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
            '50': 'f23905b0248d76f0fc8316692cd64753',
            '51': '49f82c1cac8e4bd4941ca160fcbee93d',
            '52': '4963e68ca12918d3a3eae56054214191',
            '53': '4230279ecca4f0cde652a219e10327e7',
            '54': '3068cbe488075ae166e23ea6cd29cf0f',
            '55': 'ad97f8c86cee7be9d6ab13724b55fa1c',
            '56': '5d198f40f0f1cbf9cdf1bf3de842e534',
            '57': '44dec95a0ef56c4786785f575ac59a60',
            '58': 'c59949bcfd0d68b4f272bc05a91d4dc6',
            '59': '7e09c6b177345a81439fe0aa9a2d15fc',
            '60': 'ba14bf3ddc8e182adb49eb50ae117f3e',
            '61': '94bc49170d98e0cfe59db487911ecb9d',
            '62': 'ba6c2d9f1757da31e804b92cab09dc17',
            '63': '926f05ef0acadfa4ea75fd1d94c8489c',
            '64': 'bbb3c4d8c2cba35c48380d34f122f750',
            '65': 'd453c23413627594f3f05c984e339706',
            '66': 'fe1b9e18d7fc03fac6ff4e039ace5b0b',
            '67': '78b1814e55fdaf40e753fd523d059f8d',
            '68': '4db5c00b9304ee9bc3e5dff8e87c79fd',
            '69': '292290a2fb1f5fc919291dc3949cdf7c',
            '70': '5a44bc6daf7e0ace7996904cde6d2709',
            '71': '559227e04b8fa86e0374dbed6a228109',
            '72': 'ed967195ce0e78bf2ab7245aaf0649d6',
            '73': '1db5b6bbacbfd735849221a0a9fb982e',
            '74': '85d6033ff4bb1b5eed88909ff692c775',
            '75': 'a8c58a02395db013764361692cebe5aa'
        }

        if self.Version not in hashes:
            raise Exception('Version %s is not supported' % self.Version)

        with codecs.open(dockerfile, mode='r', encoding='utf-8') as df:
            commands = df.read()
            commands = re.sub('@VERSION@', '7.' + self.Version, commands)
            commands = re.sub('@HASH@', hashes[self.Version], commands)
        with codecs.open(dockerfile, mode='w', encoding='utf-8') as df:
            df.write(commands)


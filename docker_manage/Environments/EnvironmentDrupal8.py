import codecs
import re
from . import *


class EnvironmentDrupal8(EnvironmentPHP, IEnvironment):
    skipDocumentRoot = True
    Version = '3.4'
    VendorDir = False

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = 'http_drupal8'
        self.ImitateHTTPS = self.HTTPS

        super(EnvironmentDrupal8, self).__init__(conf, owner)

        if not 'SitesDir' in conf or not Param.isValidRelPath(conf['SitesDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['SitesDir']):
            raise Exception('SitesDir is missing or invalid')
        self.Mounts.append({"Host": conf['SitesDir'], "Guest": '/var/www/html/sites', "Rights": "rw"})

        if not 'ModulesDir' in conf or not Param.isValidRelPath(conf['ModulesDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['ModulesDir']):
            raise Exception('ModulesDir is missing or invalid')
        self.Mounts.append({"Host": conf['ModulesDir'], "Guest": '/var/www/html/modules', "Rights": "rw"})

        if not 'ThemesDir' in conf or not Param.isValidRelPath(conf['ThemesDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['ThemesDir']):
            raise Exception('ThemesDir is missing or invalid')
        self.Mounts.append({"Host": conf['ThemesDir'], "Guest": '/var/www/html/themes', "Rights": "rw"})

        if not 'ProfilesDir' in conf or not Param.isValidRelPath(conf['ProfilesDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['ProfilesDir']):
            raise Exception('ProfilesDir is missing or invalid')
        self.Mounts.append({"Host": conf['ProfilesDir'], "Guest": '/var/www/html/profiles', "Rights": "rw"})

        if not 'LibrariesDir' in conf or not Param.isValidRelPath(conf['LibrariesDir']) or not Param.isValidDir(
                                self.BaseDir + '/' + conf['LibrariesDir']):
            raise Exception('LibrariesDir is missing or invalid')
        self.Mounts.append({"Host": conf['LibrariesDir'], "Guest": '/var/www/html/libraries', "Rights": "rw"})

        if 'HtaccessFile' in conf and Param.isValidFile(self.BaseDir + '/' + conf['HtaccessFile']):
            self.Mounts.append({"Host": conf['HtaccessFile'], "Guest": "/var/www/html/.htaccess", "Rights": "rw"})

        if 'VendorDir' in conf:
           if not Param.isValidRelPath(conf['VendorDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['VendorDir']):
               raise Exception('VendorDir is invalid')
           self.Mounts.append({"Host": conf['VendorDir'], "Guest": "/var/www/html/vendor", "Rights": "rw"})
           self.VendorDir = True

    # as Drupal environment does not have DocumentRoot it is not clear what
    # should be a base dir for aliases
    def processAliases(self, conf):
        pass

    def runHooks(self, verbose):
        super(EnvironmentPHP, self).runHooks(verbose)

        if verbose:
            print('    Setting up drupal permissions')
        self.runProcess(
            ['docker', 'exec', self.Name, 'chown', '-R', self.UserName + ':' + self.UserName, '/var/www/html'], verbose,
            '', 'Setting up permissions failed')

        if self.VendorDir:
            if verbose:
                print('    Updating composer libraries')
            self.runProcess(['docker', 'exec', '-u', 'www-data', self.Name, '/usr/local/sbin/updateLibs.sh'], verbose, '', 'Updating libs failed')

    def adjustVersion(self, dockerfile):
        hashes = {
            '0.0': '92ce9a54fa926b58032a4e39b0f9a9f1',
            '0.1': '423cc4d28da066d099986ac0844f6abb',
            '0.2': '9c39dec82c6d1a6d2004c30b11fb052e',
            '0.3': '7d5f5278a870b8f4a29cda4fe915d619',
            '0.4': '7516dd4c18415020f80f000035e970ce',
            '0.5': 'c13a69b0f99d70ecb6415d77f484bc7f',
            '0.6': '952c14d46f0b02bcb29de5c3349c19ee',
            '1.0': 'a6bf3c366ba9ee5e0af3f2a80e274240',
            '1.1': '529f3d72964c612695f68e0a6078b8ae',
            '1.2': '91fdfbd1c28512e41f2a61bf69214900',
            '1.3': 'f2eef421c2a0610b32519f8f2e094b7c',
            '1.4': '8c07b855ffd028124eb8848526abf4d9',
            '1.5': '0b30a3711d922c5348d6119e5124243b',
            '1.6': 'f3fdd2f9266938c2c7afc091e8d6e6d1',
            '1.7': '19e95079e50dd3c19222b91ef1b57036',
            '1.8': '7c00b318590a22f2df7a18cf70df06dc',
            '1.9': '4de7c001ecbd5c27e5837c97e40facc2',
            '1.10': 'ce373a1a7a075ff9035b1c95f54170a4',
            '2.0': '5d0c57d2fd6338d60a5e311acc188b44',
            '2.1': 'ad5ab19697ee0f7d786184ceaa7ddf6a',
            '2.2': '63d69922376a69068efb46ab4059dc34',
            '2.3': '683ddc33077bb1f7cc795607d114144e',
            '2.4': '288aa9978b5027e26f20df93b6295f6c',
            '2.5': '4bfd35c34ce1b4ba5bac2d18e0d6b5c9',
            '2.6': '57526a827771ea8a06db1792f1602a85',
            '2.7': '10b1669f750a9996096e76059c157b9a',
            '3.0': '1dcce599eddba07eb00e8879937525c3',
            '3.1': '0287dcda619e440f6d41b1cc48a81e56',
            '3.2': 'd1fce1ec78ca1bcde4a346f4c06531b4',
            '3.3': 'eafff06bbe636b526ab17c064fdc5422',
            '3.4': '243a2e10032abaf55c10a96555315727'
        }

        if self.Version not in hashes:
            raise Exception('Version %s is not supported' % self.Version)

        with codecs.open(dockerfile, mode='r', encoding='utf-8') as df:
            commands = df.read()
            commands = re.sub('@VERSION@', '8.' + self.Version, commands)
            commands = re.sub('@HASH@', hashes[self.Version], commands)
        with codecs.open(dockerfile, mode='w', encoding='utf-8') as df:
            df.write(commands)


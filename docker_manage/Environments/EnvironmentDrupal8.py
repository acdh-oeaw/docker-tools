import codecs
import re
from . import *


class EnvironmentDrupal8(EnvironmentPHP, IEnvironment):
    skipDocumentRoot = True
    Version = '7.6'
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

    # allow to serve the site using aliases
    def processAliases(self, conf):
        if not isinstance(conf, list):
            conf = [conf]

        for alias in conf:
            if not Param.isValidAlias(alias):
                raise Exception(str(len(self.Aliases) + 1) + ' alias name is missing or invalid')
            self.Aliases.append(alias)

    def getAliases(self):
        aliases = ''
        for alias in self.Aliases:
            aliases += 'Alias ' + alias + ' /var/www/html\n'
        return aliases

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
            '3.4': '243a2e10032abaf55c10a96555315727',
            '3.5': '23832fcfe0c6398727d24e582042f149',
            '3.6': 'de7ceedf9391c4b52c1c5a7f66809129',
            '3.7': 'e7b1f382d6bd2b18d4b4aca01d335bc0',
            '3.8': '94cc223abff93a33762041a1fb2f7c3a',
            '3.9': 'b53f505b0243d608b6a6550ae664bc75',
            '4.0': '074795a2f5fc0b599a7dcfb9d1fb03f5',
            '4.1': '1c1db36ac5217f315bf9c03d64529f10',
            '4.2': 'a2b294d82ce751f93ba600f2de7884f4',
            '4.3': '55a53cb43284b3d710a2742d458fc1da',
            '4.4': 'cfce3fb9293d8fe146f4c000505cb9b6',
            '4.5': 'e866ae73a2ce13eb803cd24c68ef94c7',
            '4.6': 'e4b17dc542724f6298435dca81a84f8d',
            '4.7': '965b59360079fab9020fffce8c09a994',
            '4.8': 'f922c5fead1e05ecf155cfd63983fcf1',
            '5.0': '5679d3fa188fb80368ee46ab40acdb6b',
            '5.1': '23e18afbdd031d0cd7c519c4e9baff71',
            '5.2': 'c85c6ec800100d458fad6b9469e2fd8b',
            '5.3': 'aedc6598b71c5393d30242b8e14385e5',
            '5.4': '4237ee4c5384bd90ed8dc4fa0ed3bb0c',
            '5.5': '4fee1348bbac85cae82d6634e7296b9f',
            '5.6': '1e789adb03cf2a82a9c3bced67c02328',
            '5.7': 'a5f35336995ed209a917a4370e0c34d7',
            '5.8': '9642e018a0b0ed7bd8a3472fa0b64ccd',
            '5.9': 'ab7feda97f750c8997154c04ee7b1c5b',
            '5.10': '39e2b451d6bc6f58c4eeb09ad26ad965',
            '5.11': '356333785c71215d2e3ec0d4a4e018df',
            '5.12': '91b4b708c231b098a52b15501ac3c4cf',
            '5.13': '31fc4a473b2096284969ff2d2590323e',
            '5.14': '9f3035984039e0a5de0ce899722b9941',
            '5.15': '7a4ba499132c834e5d33bccae5ac1430',
            '6.0': '6d457c7e478574a5125f608f3d6b7fa5',
            '6.1': 'fad034b129695c5066e892cd7cb02a11',
            '6.2': '46a42d70047dafd4b05e3dd050cea887',
            '6.3': '3a3b8e4326b493ed6c29188db40031ff',
            '6.4': '455722dcf2c051232e6f9299725d11a3',
            '6.5': '3db4ab3674ae38d1b15d5faac3b10ff0',
            '6.6': 'bdabe7ae149890555e176ba492b7b250',
            '6.7': 'cd3d0c9ad1d9e976eb589a963e427388',
            '6.8': '5c8f5107e3831f6e6f55f17486dee5d2',
            '6.9': '9455aeacf1faf24b3a12890a50198a5e',
            '6.10': '5aee2dacfb525f146fc28b4535066d1c',
            '6.11': '9c2b33438b29df0395ff751b78cd1655',
            '6.12': '0bc838e3e3155141a9496481c382c182',
            '6.13': 'ded84151ebda80826f18e924dab03edd',
            '6.14': '04cf60554a5036c7a69c652e669461c3',
            '6.15': '85ae6b9f7309cc8564331fd77369dffd',
            '6.16': 'a0683ae0b0ea99845a6bf45383671cb9',
            '6.17': '9018a2d11381aeb0e269ca696fed9ac5',
            '7.0': 'f6135e49de6bc5b1f259ef3e76580dd0',
            '7.1': '2cf2a1c93ea785c6ff91d29aebef2697',
            '7.2': 'f637a19f7d087e9f68e39470fd151a1d',
            '7.3': 'bba896a1ed2fbe4a1744d82c036fcfc4',
            '7.4': '5bd5db96c8a4d017e940a43285f5166b',
            '7.5': '39cc326d9db1b4acce9b8716193189fd',
            '7.6': '484530915cbf6d96cb03379e3dda018e'


        }

        if self.Version not in hashes:
            raise Exception('Version %s is not supported' % self.Version)

        with codecs.open(dockerfile, mode='r', encoding='utf-8') as df:
            commands = df.read()
            commands = re.sub('@VERSION@', '8.' + self.Version, commands)
            commands = re.sub('@HASH@', hashes[self.Version], commands)
        with codecs.open(dockerfile, mode='w', encoding='utf-8') as df:
            df.write(commands)


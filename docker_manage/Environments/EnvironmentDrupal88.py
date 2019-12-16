import codecs
import re
from . import *


class EnvironmentDrupal88(EnvironmentApache, IEnvironment):
    skipDocumentRoot = True
    UserName = 'www-data'
    GroupName = 'www-data' 

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = 'http_drupal88'
        self.ImitateHTTPS = self.HTTPS

        super(EnvironmentDrupal88, self).__init__(conf, owner)

        if not 'SitesDir' in conf or not Param.isValidRelPath(conf['SitesDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['SitesDir']):
            raise Exception('SitesDir is missing or invalid')
        self.Mounts.append({"Host": conf['SitesDir'], "Guest": '/var/www/drupal/git/web/sites', "Rights": "rw"})

        if not Param.isValidRelPath(conf['ComposerDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['ComposerDir']):
            raise Exception('ComposerDir is invalid')
        self.Mounts.append({"Host": conf['ComposerDir'], "Guest": "/var/www/drupal/composer", "Rights": "rw"})

        if 'ModulesDir' in conf:
            if not 'ModulesDir' in conf or not Param.isValidRelPath(conf['ModulesDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['ModulesDir']):
                raise Exception('ModulesDir is missing or invalid')
            self.Mounts.append({"Host": conf['ModulesDir'], "Guest": '/var/www/drupal/git/web/modules/custom', "Rights": "rw"})

        if 'ThemesDir' in conf:
            if not 'ThemesDir' in conf or not Param.isValidRelPath(conf['ThemesDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['ThemesDir']):
                raise Exception('ThemesDir is missing or invalid')
            self.Mounts.append({"Host": conf['ThemesDir'], "Guest": '/var/www/drupal/git/web/themes/custom', "Rights": "rw"})

        if 'VendorDir' in conf:
            if not Param.isValidRelPath(conf['VendorDir']) or not Param.isValidDir(self.BaseDir + '/' + conf['VendorDir']):
                raise Exception('VendorDir is invalid')
            self.Mounts.append({"Host": conf['VendorDir'], "Guest": "/var/www/drupal/git/vendor", "Rights": "rw"})

    def runHooks(self, verbose):
        # it's not a but that we are skinng EnvironmentApache runHooks()
        super(EnvironmentApache, self).runHooks(verbose)

        if verbose:
            print('    Updating composer libraries')
        self.runProcess(['docker', 'exec', '-u', 'www-data', self.Name, '/usr/bin/bash', '-c', 'cd /var/www/drupal/git && composer update'], verbose, '', 'Updating libs failed')

    def getDockerOpts(self):
        # it's not a but that we are skinng EnvironmentApache getDockerOpts()
        return super(EnvironmentApache, self).getDockerOpts()


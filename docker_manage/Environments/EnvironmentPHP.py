from . import *


class EnvironmentPHP(EnvironmentApache, IEnvironment):
    DockerfileDir = 'base_http_php'
    UserName = 'www-data'
    LogDirMount = '/var/log/apache2'
    ExecDir = None
    ExecDirMount = '/var/www/exec'
    ConfigDir = None
    ConfigDirMount = '/var/www/config'

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = self.DockerfileDir
        super(EnvironmentPHP, self).__init__(conf, owner)

        self.processLogDir(conf, True)

        if 'ExecDir' in conf:
            if (
                self.owner and (
                    not Param.isValidRelPath(conf['ExecDir'])
                    or not Param.isValidDir(self.BaseDir + '/' + conf['ExecDir'])
                )
            ):
                raise Exception('ExecDir is invalid')
            self.ExecDir = conf['ExecDir']

        if 'ConfigDir' in conf:
            if (
                self.owner and (
                    not Param.isValidRelPath(conf['ConfigDir'])
                    or not Param.isValidDir(self.BaseDir + '/' + conf['ConfigDir'])
                )
            ):
                raise Exception('ConfigDir is invalid')
            self.ConfigDir = conf['ConfigDir']

        # Omar's personal stuff
        if self.ExecDir is not None:
            self.Mounts.append({"Host": self.ExecDir, "Guest": self.ExecDirMount, "Rights": "rw"})
        if self.ConfigDir is not None:
            self.Mounts.append({"Host": self.ConfigDir, "Guest": self.ConfigDirMount, "Rights": "rw"})

class EnvironmentPHPL(EnvironmentPHP, IEnvironment):
    DockerfileDir = 'http_php_latest'
    guestVHTemplate = """
<VirtualHost *:80>
  ServerName {ServerName}
  DocumentRoot {DocumentRootMount}
  ServerAlias {ServerAlias}

  <Directory {DocumentRootMount}>
    Require all granted
    AllowOverride {AllowOverride}
    Options {Options}
  </Directory>

  {Aliases}
  {ImitateHTTPS}
</VirtualHost>   
"""

    def getDockerOpts(self):
        return super(EnvironmentApache, self).getDockerOpts()

class EnvironmentPHP5(EnvironmentPHP, IEnvironment):
    DockerfileDir = 'http_php5'

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = self.DockerfileDir
        super(EnvironmentPHP5, self).__init__(conf, owner)

class EnvironmentCorpusShell(EnvironmentPHP, IEnvironment):
    DockerfileDir = 'corpus_shell'

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = self.DockerfileDir
        super(EnvironmentCorpusShell, self).__init__(conf, owner)

class EnvironmentVLEServer(EnvironmentPHP, IEnvironment):
    DockerfileDir = 'vleserver'

    def __init__(self, conf, owner):
        if 'DockerfileDir' not in conf:
            conf['DockerfileDir'] = self.DockerfileDir
        super(EnvironmentVLEServer, self).__init__(conf, owner)

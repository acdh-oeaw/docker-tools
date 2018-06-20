from . import *

class Environmentjenkins(EnvironmentHTTP, IEnvironment):
  """Jenkins specific configuration
  JENKINS_HOME must be mounted from the file system
  Reverse proxy needs special settings:
  * AllowEncodedSlashes NoDecode
  * ProxyPass .... nocanon
  """

  DataDirMount       = '/var/jenkins_home'
  DataDir            = None

  def __init__(self, conf, owner):
    self.AllowEncodedSlashes = "NoDecode"
    self.ProxyOptions = "nocanon"
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'jenkins'
    super(Environmentjenkins, self).__init__(conf, owner)
    if (
        not 'JenkinsHome' in conf
        or self.owner and (
          not Param.isValidRelPath(conf['JenkinsHome'])
          or not Param.isValidDir(self.BaseDir + '/' + conf['JenkinsHome'])
        )
      ) :
        raise Exception('JenkinsHome is missing or invalid')
    self.DataDir = conf['JenkinsHome']
    self.Mounts.append({ "Host" : self.DataDir, "Guest" : self.DataDirMount, "Rights" : "rw" })
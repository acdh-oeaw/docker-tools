import subprocess
import distutils

from . import *
from ..HTTPReverseProxy import HTTPReverseProxy

class EnvironmentNoske(EnvironmentHTTP, IEnvironment):
  DataPath = 'data'
  BonitoPath = 'bonito'
  RegistryPath = 'registry'

  def __init__(self, conf, owner):
    if 'DockerfileDir' not in conf :
      conf['DockerfileDir'] = 'noske'
    super(EnvironmentNoske, self).__init__(conf, owner)
    self.Mounts.append({"Host" : self.BaseDir + '/' + self.DataPath, "Guest" : "/data", "Rights" : "ro"})
    self.Ports = [{ "Host" : HTTPReverseProxy.getPort(), "Guest" : 80 , "Type" : "HTTP", "ws" : [], "Alias" : ""}]

    #TODO It would be nice to allow users to provide DataPath, BonitoPath and RegistryPath through the conf variable
    # Of course values provided by the user should be checked - the Param class provides useful methods to perform such checks

  def runHooks(self, verbose):
    super(EnvironmentNoske, self).runHooks(verbose)

    #TODO we should rather use self.runProcess() instead of subprocess.call() to handle verbose flag and error handling in an easy way
    subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/usr/lib/python2.7/dist-packages/bonito'])
    distutils.dir_util.copy_tree(self.BaseDir + '/' + self.BonitoPath, self.DockerMntBase + '/' + self.Name + '/usr-lib-python2.7-dist-packages-bonito')
    subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/usr/lib/python2.7/dist-packages/bonito'])
    subprocess.call(['docker', 'exec', self.Name, 'chmod', '+rX', '-R', '/usr/lib/python2.7/dist-packages/bonito'])
    subprocess.call(['docker', 'exec', self.Name, 'python', '-m', 'compileall', '/usr/lib/python2.7/dist-packages/bonito']) 

    subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/var/lib/manatee/registry/'])
    distutils.dir_util.copy_tree(self.BaseDir + '/' + self.RegistryPath, self.DockerMntBase + '/' + self.Name + '/var-lib-manatee-registry/')
    subprocess.call(['docker', 'exec', self.Name, 'chown', 'user:user', '-R', '/var/lib/manatee/registry/'])
    subprocess.call(['docker', 'exec', self.Name, 'chmod', '+rX', '-R', '/var/lib/manatee/registry/'])

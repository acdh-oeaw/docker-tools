from . import *

class EnvironmentSketchEngine(EnvironmentSkeBase, IEnvironment):
  UserName          = 'apache'
  DataDirMount      = '/corpora/data'
  BonitoDirMount    = '/var/lib/ske'
  RegistryDirMount  = '/corpora/registry'
  BonitoLibDirMount = '/usr/lib/python2.7/site-packages/bonito'
  Auth              = False

  def __init__(self, conf, owner):
    if not 'DockerfileDir' in conf :
      conf['DockerfileDir'] = 'sketch-engine'
    super(EnvironmentSketchEngine, self).__init__(conf, owner)

    if 'Auth' in conf :
      if not isinstance(conf['Auth'], basestring) or not ['true', 'false'].count(conf['Auth']) > 0 :
        raise Exception('Auth is not a string or has value other then true/false')
      self.Auth = conf['Auth'] == 'true'

    try:
      self.getHTTPPort()
    except:
      self.Ports.append({ "Host" : HTTPReverseProxy.getPort(), "Guest" : 80 , "Type" : "HTTP", "ws" : [], "Alias" : ""})

    self.Mounts.append({"Host" : self.RegistryDir, "Guest" : "/var/lib/ske/registry", "Rights" : "rw"})

  def runHooks(self, verbose):
    super(EnvironmentSketchEngine, self).runHooks(verbose)

    if verbose :
      print '    Reconfiguring Apache Alias'
    self.runProcess(['docker', 'exec', self.Name, 'sed', '-i', '-e', 's/DocumentRoot "\/var\/www\/html.*"/DocumentRoot "\/var\/www\/bonito"/', '/etc/httpd/conf/httpd.conf'], False, '', 'Apache reconfiguration failed')
    self.runProcess(['docker', 'exec', self.Name, 'apachectl', '-k', 'graceful'], False, '', 'Apache reconfiguration failed')

    # we are using system's apache account with adjusted UID, thus we must also adjust files ownership because here and now they are owned by an orphaned UID
    if verbose :
      print '    Adjusting files ownership'
    self.runProcess(['docker', 'exec', self.Name, 'chown', '-R', self.UserName, '/var/www/bonito', '/usr/share/httpd'], False, '', 'ownership adjustment failed')

    if self.Auth:
      if verbose:
        print '    Enabling authentication'
      self.runProcess(['docker', 'exec', self.Name, 'sed', '-i', '-e', 's/^#//', '/var/www/bonito/.htaccess'], False, '', 'Authentication enabling failed')

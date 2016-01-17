import subprocess
import re

class HTTPReverseProxy(object):
  portNumber = 8020

  @staticmethod
  def getPort():
    HTTPReverseProxy.portNumber += 1

    # find first free port
    ports = subprocess.check_output(['/bin/netstat', '-lt', '--numeric-ports'])
    while re.search(':' + str(HTTPReverseProxy.portNumber) + ' ', ports) :
      HTTPReverseProxy.portNumber += 1

    return HTTPReverseProxy.portNumber

import re
import os
import subprocess

class Param(object):
  # see http://stackoverflow.com/questions/53497/regular-expression-that-matches-valid-ipv6-addresses#17871737
  # there are comments on small shortcommings
  IPV4SEG  = "(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])"
  IPV4ADDR = "(%(IPV4SEG)s\.){3,3}%(IPV4SEG)s" % {"IPV4SEG": IPV4SEG}
  IPV4ADDRpart = "(%(IPV4SEG)s\.){1,3}%(IPV4SEG)s" % {"IPV4SEG": IPV4SEG}
  IPV6SEG  = "[0-9a-fA-F]{1,4}"
  IPV6ADDR = ("("
         "(%(IPV6SEG)s:){7,7}%(IPV6SEG)s|"                # 1:2:3:4:5:6:7:8
         "(%(IPV6SEG)s:){1,7}:|"                          # 1::                                 1:2:3:4:5:6:7::
         "(%(IPV6SEG)s:){1,6}:%(IPV6SEG)s|"               # 1::8               1:2:3:4:5:6::8   1:2:3:4:5:6::8
         "(%(IPV6SEG)s:){1,5}(:%(IPV6SEG)s){1,2}|"        # 1::7:8             1:2:3:4:5::7:8   1:2:3:4:5::8
         "(%(IPV6SEG)s:){1,4}(:%(IPV6SEG)s){1,3}|"        # 1::6:7:8           1:2:3:4::6:7:8   1:2:3:4::8
         "(%(IPV6SEG)s:){1,3}(:%(IPV6SEG)s){1,4}|"        # 1::5:6:7:8         1:2:3::5:6:7:8   1:2:3::8
         "(%(IPV6SEG)s:){1,2}(:%(IPV6SEG)s){1,5}|"        # 1::4:5:6:7:8       1:2::4:5:6:7:8   1:2::8
         "%(IPV6SEG)s:((:%(IPV6SEG)s){1,6})|"             # 1::3:4:5:6:7:8     1::3:4:5:6:7:8   1::8
         ":((:%(IPV6SEG)s){1,7}|:)|"                      # ::2:3:4:5:6:7:8    ::2:3:4:5:6:7:8  ::8       ::
         "fe80:(:%(IPV6SEG)s){0,4}%%[0-9a-zA-Z]{1,}|"     # fe80::7:8%eth0     fe80::7:8%1  (link-local IPv6 addresses with zone index)
         "::(ffff(:0{1,4}){0,1}:){0,1}%(IPV4ADDR)s|"      # ::255.255.255.255  ::ffff:255.255.255.255  ::ffff:0:255.255.255.255 (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
         "(%(IPV6SEG)s:){1,4}:%(IPV4ADDR)s"               # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
         ")") % {"IPV6SEG": IPV6SEG, "IPV4ADDR": IPV4ADDR}
  reIPV6ADDR = re.compile("^"+IPV6ADDR+"$")
  reIPV4ADDR = re.compile("^"+IPV4ADDRpart+"$")
  IPV4NETMASK = IPV4ADDR+"/(3[0-2]|[12][0-9]|[0-9])"
  reIPV4NETMASK = re.compile("^"+IPV4NETMASK+"$")
  IPV6NETMASK = IPV6ADDR+"/(1[0-2][0-8]|1[0-1]9|[0-9][0-9])"
  reIPV6NETMASK = re.compile("^"+IPV6NETMASK+"$")
  @staticmethod
  def isValidAbsPath(p):
    return not re.search('/[.][.]/', p) and re.search('^/[-_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidRelPath(p):
    return (not (re.search('^/', p) or re.search('^[.][.]/', p) or re.search('/[.][.]/', p))) and re.search('^[-/_.:a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidFile(p):
    return os.path.isfile(p)

  @staticmethod
  def isValidDir(p):
    return os.path.isdir(p)

  @staticmethod
  def isValidName(p):
    return re.search('^[-_.a-zA-Z0-9]+$', p)

  @staticmethod
  def isValidNumber(p):
    return re.search('^[0-9]+$', str(p))

  @staticmethod
  def isValidDomain(p):
    return re.search('^((([a-z0-9][-a-z0-9]*[a-z0-9])|([a-z0-9]+))[.]?)+$', str(p))

  @staticmethod
  def isValidAlias(p):
    return re.search('^/[-_.a-zA-Z0-9/]+$', str(p))

  @staticmethod
  def isValidHostName(p):
    return re.search('^([-a-zA-Z0-9][.]?)+$', p)

  @staticmethod
  def isValidIP(p):
    return (
      Param.reIPV4ADDR.search(str(p))
      or Param.reIPV6ADDR.search(str(p))
    )

  @staticmethod
  def isValidRequireIP(p):
    return (
      Param.reIPV4ADDR.search(str(p))
      or Param.reIPV4NETMASK.search(str(p))
      or Param.reIPV6ADDR.search(str(p))
      or Param.reIPV6NETMASK.search(str(p))
    )

  @staticmethod
  def isValidParamsList(p):
    if not isinstance(p, list) :
      return False
    for i in p:
      if not isinstance(i, basestring) :
        return False
    return True

  @staticmethod
  def isValidVarName(p):
    return re.search('^[_a-zA-Z][_a-zA-Z0-9]*$', str(p))

  @staticmethod
  def isValidRe(p):
    try:
      re.compile(p)
      return True
    except re.error as e:
      return False

  @staticmethod
  def getSecurityContext(p):
    proc = subprocess.Popen(['ls', '-Z', p], stdout = subprocess.PIPE)
    out = proc.communicate()[0]
    out = out[:-(2 + len(p))]
    out = out.split(' ').pop().split(':')[-2:-1][0]
    return out


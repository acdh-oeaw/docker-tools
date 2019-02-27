import json
import re
import subprocess


class NetworkRange(object):
    """ Class handling available Docker private networks IP4 ranges

    Assumes Docker private networks reside in the 20-bit 172.16.0.0/20 address space
    """

    addrSpace = None

    def __init__(self):
        self.addrSpace = [(0, 1048575)]
        nets = subprocess.check_output(['docker', 'network', 'ls']).rstrip().split('\n')

        ranges = []
        for net in nets[1:]:
            out = subprocess.check_output(['docker', 'network', 'inspect', re.sub(' .*$', '', net)])
            for cfg in json.loads(out)[0]['IPAM']['Config']:
                rng = self.toRange(cfg['Subnet'])
                self.reserveRange(rng)

    def getSubnet(self, size):
        size = int(size)
        count = 1 << size # convert from bits to number of addresses
        for rng in self.addrSpace:
            if rng[1] - rng[0] + 1 >= count:
                newRng = (rng[0], rng[0] + count - 1)
                self.reserveRange(newRng)
                o4 = newRng[0] % 256
                o3 = int(newRng[0] / 256) % 256
                o2 = 16 + int(newRng[0] / 65536)
                return '172.%d.%d.%d/%d' % (o2, o3, o4, 32 - size)

    def reserveRange(self, rng):
        i = 0
        while i < len(self.addrSpace) and self.addrSpace[i][0] <= rng[0]:
            i += 1
        i -= 1
        new = []
        if rng[0] > self.addrSpace[i][0]:
            new.append((self.addrSpace[i][0], rng[0] - 1))
        if rng[1] < self.addrSpace[i][1]:
            new.append((rng[1] + 1, self.addrSpace[i][1]))
        self.addrSpace = self.addrSpace[0:i] + new + self.addrSpace[(i + 1):]

    def toRange(self, subnet):
        ip, mask = subnet.split('/')
        tmp = [int(x) for x in ip.split('.')]
        first = tmp[3] + tmp[2] * 256 + (tmp[1] & 15) * 65536
        last = first + (1 << (32 - int(mask))) - 1
        return (first, last)


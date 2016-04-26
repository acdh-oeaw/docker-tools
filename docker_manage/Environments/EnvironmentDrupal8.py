import codecs
import re
from . import *


class EnvironmentDrupal8(EnvironmentDrupal7, IEnvironment):
    def __init__(self, conf, owner):
        super(EnvironmentDrupal8, self).__init__(conf, owner)

    def adjustVersion(self, dockerfile):
        hashes = {
            '0.0': '92ce9a54fa926b58032a4e39b0f9a9f1',
            '0.1': '423cc4d28da066d099986ac0844f6abb',
            '0.2': '9c39dec82c6d1a6d2004c30b11fb052e',
            '0.3': '7d5f5278a870b8f4a29cda4fe915d619',
            '0.4': '7516dd4c18415020f80f000035e970ce',
            '0.5': 'c13a69b0f99d70ecb6415d77f484bc7f',
            '0.6': '952c14d46f0b02bcb29de5c3349c19ee',
            '1.0': 'a6bf3c366ba9ee5e0af3f2a80e274240'
        }

        if self.Version not in hashes:
            raise Exception('Version %s is not supported' % self.Version)

        with codecs.open(dockerfile, mode='r', encoding='utf-8') as dockerfile:
            commands = dockerfile.read()
            commands = re.sub('@VERSION@', '8.' + self.Version, commands)
            commands = re.sub('@HASH@', hashes[self.Version], commands)
        with codecs.open(dockerfile, mode='r', encoding='utf-8') as dockerfile:
            dockerfile.write(commands)

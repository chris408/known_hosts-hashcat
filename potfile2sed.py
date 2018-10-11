#!/usr/bin/env python3
import sys, re
from base64 import b64encode
from codecs import decode

def main(self, potfile=sys.stdin):
    if potfile in ('-h', '--help'):
        print("usage: {} <potfile>".format(self))
        return
    if potfile is not sys.stdin:
        potfile = open(potfile, 'r')
    print_sed_script(map(convert1, read_pot_file(potfile)))

def read_pot_file(potfile):
    rex = re.compile(r"^([0-9a-fA-F]+):([0-9a-fA-F]+):(.*)$")
    return map(lambda m: m.groups(), filter(None, [
        re.match(rex, line)
        for line in potfile
    ]))

def convert1(matchgroups):
    (hash, salt, plain) = matchgroups
    return '''s@|1|{}|{}@{}@g'''.format(
        decode(b64encode(decode(salt, 'hex')), 'utf-8'),
        decode(b64encode(decode(hash, 'hex')), 'utf-8'),
        plain
    )

def print_sed_script(substs):
    print(str.join('\n', substs))

if __name__ == "__main__":
    sys.exit(main(*sys.argv))

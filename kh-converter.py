#!/usr/bin/env python3
import sys
import base64
import re
import codecs

def main(kh_file):
    kh = readkh(kh_file)
    output = convertkh(kh)
    printOutput(output)

def printOutput(output):
    for line in output:
        print(line)

def convertkh(kh):
    output = []
    for line in kh:
        line = (codecs.decode(codecs.encode(base64.b64decode(line[1]), "hex"), ("utf-8")) + ":" +
                codecs.decode(codecs.encode(base64.b64decode(line[0]), "hex"), ("utf-8")))
        output.append(line)
    return output

def readkh(kh_file):
    try:
        restring = re.compile("\|1\|(.*?)\|(.*?)\s")
        kh = re.findall(restring, open(kh_file).read())
    except:
        print("Unable to open known_hosts file: %s" % kh_file)
    return kh

if __name__ == '__main__':
    if(len(sys.argv) != 2):
        print("Usage: python3 known_hosts-converter.py <known_hosts file>")
        exit()
    else:
        main(sys.argv[1])

from configparser import RawConfigParser
import os
import sys

folder = os.path.dirname(os.path.realpath(sys.argv[0]))

config = RawConfigParser()
config.read(os.path.join(folder, 'output_format.ini'))
config.read(os.path.join(folder, 'theme.ini'))

def get(section, item):
    return config.get(section, item)

def items(section):
    return config.items(section)

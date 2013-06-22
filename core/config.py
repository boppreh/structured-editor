try:
    from configparser import RawConfigParser
except:
    from ConfigParser import RawConfigParser
import os
import sys
from collections import defaultdict

folder = os.path.dirname(os.path.realpath(sys.argv[0]))

config = RawConfigParser()
config.read(os.path.join(folder, 'output_format.ini'))
config.read(os.path.join(folder, 'theme.ini'))

def get(section, item, default=''):
    try:
        return config.get(section, item)
    except:
        return default

def section(section_name):
    try:
        return defaultdict(str, config.items(section_name))
    except:
        return defaultdict(str)

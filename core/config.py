from ConfigParser import RawConfigParser

config = RawConfigParser()
config.read('output_format.ini')
config.read('theme.ini')

def get(section, item):
    return config.get(section, item)

def items(section):
    return config.items(section)

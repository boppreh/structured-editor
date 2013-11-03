from .structures import *
from ast import parse

def parse_string(string):
    return parse(string)

def new_empty():
    return parse_string('')

structures = []
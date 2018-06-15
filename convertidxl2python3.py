from sys import *
import re
import ast
import lexer
import parser
import generator

def open_file(filename):
    f = open(filename, 'r')
    rawcontents = f.readlines()
    rawcontents = [x.strip('\n') for x in rawcontents]
    return rawcontents

def run():
    contents = open_file(argv[1])
    toks = lexer.lex(contents)
    #parse.parse(toks)
    #generator.generate()

run()

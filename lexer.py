from sys import *
import re
from itertools import tee, islice, chain

def previous_and_next(some_iterable):
    prevs, items, nexts = tee(some_iterable, 3)
    prevs = chain([None], prevs)
    nexts = chain(islice(nexts, 1, None), [None])
    return zip(prevs, items, nexts)

tokens = []
token_types = []
prev = next_ = None

def lex(filecontents):
    token = ""
    state = ""
    for prevline, line, nextline in previous_and_next(filecontents):
        if state == "sql_extended":
            token += line
            if nextline.endswith(';'):
                token += nextline
                tokens.append(token)
                state = ""
        if line.endswith(':'):
            token_types.append("SECTION")
            tokens.append(line)
        if line.startswith('#'):
            token_types.append("COMMENT")
            tokens.append(line)
            continue
        if line.startswith('set'):
            token_types.append("VARIABLE")
            tokens.append(line)
            continue
        if line.startswith('find'):
            token_types.append("FIND")
            tokens.append(line)
            continue
        if line.startswith('gosub'):
            token_types.append("GOSUB")
            tokens.append(line)
            continue
        if line.startswith('tell'):
            token_types.append("TELL")
            tokens.append(line)
        if line.startswith('calc'):
            token_types.append("CALC")
            tokens.append(line)
        if line.startswith('parse'):
            token_types.append("PARSE")
            tokens.append(line)
        if line.startswith('on'):
            token_types.append("ON")
            tokens.append(line)
        if line.startswith('rewind'):
            token_types.append("REWIND")
            tokens.append(line)
        if line.startswith('skip'):
            token_types.append("SKIP")
            tokens.append(line)
        if line.startswith('include'):
            token_types.append("INCLUDE")
            tokens.append(line)

        #special case sql can be many lines. Terminated by ';'
        if line.startswith('sql'):
            token_types.append("SQL")
            token += line
            print("TOKEN: ", token)
            if nextline.endswith(';'):
                token += nextline
                tokens.append(token)
                state = ""
            else:
                state = "sql_extended"

        #special case if statements can be many lines. Terminated by 'endif'
        # if line.startswith('if'):
        #     token_types.append('IF CONTROL')
        # while line != 'endif':
        #     continue
        #     tokens.append(line)

    print("TOKENS: ", tokens)
    print('\n')
    print("TOKEN_TYPES: ", token_types)
    return tokens, token_types

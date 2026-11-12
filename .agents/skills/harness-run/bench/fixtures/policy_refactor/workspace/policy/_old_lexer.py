"""Legacy character scanner. Tokens are internal triples, not public Tokens."""


def tokenize(source):
    if not isinstance(source, str):
        raise TypeError('source must be str')
    result = []
    index = 0
    size = len(source)
    while index < size:
        char = source[index]
        start = index
        if char.isspace():
            index += 1
            continue
        if char == '#':
            break
        if char in ('"', "'"):
            quote = char
            index += 1
            value = ''
            while index < size:
                char = source[index]
                index += 1
                if char == quote:
                    break
                if char == '\\':
                    if index == size:
                        raise SyntaxError(f'unterminated escape at {start}')
                    char = source[index]
                    index += 1
                    if char == 'n':
                        char = '\n'
                    elif char == 'r':
                        char = '\r'
                    elif char == 't':
                        char = '\t'
                value += char
            else:
                raise SyntaxError(f'unterminated string at {start}')
            result.append(('value', value, start))
            continue
        if '0' <= char <= '9':
            index += 1
            while index < size and '0' <= source[index] <= '9':
                index += 1
            result.append(('value', int(source[start:index]), start))
            continue
        if char == '_' or 'a' <= char <= 'z' or 'A' <= char <= 'Z':
            index += 1
            while index < size:
                next_char = source[index]
                if not (next_char == '_' or 'a' <= next_char <= 'z' or
                        'A' <= next_char <= 'Z' or '0' <= next_char <= '9'):
                    break
                index += 1
            word = source[start:index]
            if word == 'true':
                result.append(('value', True, start))
            elif word == 'false':
                result.append(('value', False, start))
            elif word == 'null':
                result.append(('value', None, start))
            else:
                result.append(('word', word, start))
            continue
        pair = source[index:index+2]
        if pair in ('==', '!=', '<=', '>='):
            result.append(('symbol', pair, start))
            index += 2
        elif char in '<>(),':
            result.append(('symbol', char, start))
            index += 1
        else:
            raise SyntaxError(f'unexpected character at {start}')
    result.append(('end', None, size))
    return result

from .exceptions import Location, LexerSetupError

def group(token, *group_names):
    groupdict = token.lexer.lexmatch.groupdict()

    if len(group_names) == 1:
        return groupdict[group_names[0]]
    else:
        return [groupdict[name] for name in group_names]

groups = group

tokens = ( "name_keyword", "include_keyword",
           "identifyer",
           "number_literal", "string_literal",
           "walrus",
           "open_paren", "close_paren", "plus",
           "open_bracket", "close_bracket", "comma",
           "line_comment", "inline_comment", "whitespace", )

t_name_keyword = r"name"
t_include_keyword = r"include"

def t_identifyer(token):
    r"([^\d\W]\w*)"
    if token.value == "name":
        token.type = "name_keyword"
    elif token.value == "include":
        token.type = "include_keyword"
    elif token.value == "NULL":
        token.type = "number_literal"
        token.value = None
    return token

def t_number_literal(token):
    (r"(?P<NULL>NULL)|"
     r"0x(?P<HEX>[0-9a-zA-Z]+)|"
     r"0o(?P<OCT>[0-7]+)|"
     r"0b(?P<BIN>[01]+)|"
     r"(?P<DEC>\d+)")
    NULL, HEX, OCT, BIN, DEC = groups(token, "NULL", "HEX",
                                      "OCT", "BIN", "DEC")
    if NULL is not None:
        token.value = None
    elif HEX is not None:
        token.value = int(HEX, 16)
    elif OCT is not None:
        token.value = int(OCT, 8)
    elif BIN is not None:
        token.value = int(BIN, 2)
    else:
        token.value = int(DEC)

    return token

def t_string_literal(token):
    r'"(?P<double_quoted_string>[^"]*)"|\'(?P<single_quoted_string>[^\']*)\''
    token.value = group(token, "double_quoted_string") \
        or group(token, "single_quoted_string")

    return token

t_walrus = r":="

t_open_paren = r"\("
t_close_paren = r"\)"
t_plus = r"\+"

t_open_bracket = r"\["
t_close_bracket = r"\]"
t_comma = r","

def t_line_comment(token):
    r"\s*#.*"
    return None

def t_inline_comment(token):
    r"\s/\*[.\n\r]*\*/\s*"
    return None

def t_whitespace(token):
    r"[\s\n\r]+"
    return None

def t_error(t):
    if t is None:
        raise LexerSetupError(repr(t))

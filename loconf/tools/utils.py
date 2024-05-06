from loconf.language.parser import Parser

def read_names_file(fp):
    parser = Parser()
    parser.parse(fp)
    return dict( [(value, name,)
                  for (name, value) in parser.variables.items()] )

import re

class Tokenizer(object):

    def tokenize(self, text):
        '''
        Input text of a file, genrate tokens for the file
        Output text to write to T.xml file and tokens array including tuple of type and token
        '''
        #clean up multi-line comments and tabs
        text = re.sub("/\*.*?\*/", "", text, flags = re.DOTALL).replace("\t", " ")
        #split text into lines, filtering empty lines, one-line comments, put
        #splits into line generator
        lines = (line.strip().split("//")[0].strip() for line in text.split("\n")\
         if line.strip() and not line.strip().startswith("//"))

        for line in lines:
            n, i = len(line), 0
            token = ""
            while i <= n:
                #dealting with stringConstant
                if token == '"':
                    while line[i] != '"':
                        token += line[i]
                        i += 1
                    token += line[i]
                #white space or symbol is the cut-off between tokens, when encounter
                #white space or symbol, put current token into tokens array, move on
                #to generate next token
                elif (len(token) == 1 and token in "{}()[].,;+-*/&|<>=~") or\
                ((line[i] == " " or line[i] in "{}()[].,;+-*/&|<>=~") and token):

                    type = self.type(token)
                    token = token.replace('"', '')
                    yield (type, token)

                    if i < n:
                        #skip white space
                        if not line[i] == " ":
                            token = line[i]
                        else:
                            token = ""
                else:
                    #skip white space
                    if not line[i] == " ":
                        token += line[i]
                i += 1

    def type(self, token):
        '''
        Given token, return token type
        '''
        if token in "{}()[].,;+-*/&|<>=~":
            return "symbol"

        elif token in {"class", "constructor", "function", "method", "field", \
                        "static", "var", "int", "char", "boolean", "void", "true",\
                        "false", "null", "this", "let", "do", "if", "else", "while",\
                        "return"}:
            return "keyword"

        elif token.startswith('"'):
            return "stringConstant"

        elif token[0].isdigit():
            return "integerConstant"

        else:
            return "identifier"

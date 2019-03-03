import re
import glob
import os
import sys

class Tokenizer(object):

    def tokenize(self, text):
        '''
        input text of a file, genrate tokens for the file
        output text to write to T.xml file and tokens array including tuple of type and token
        '''
        #clean up multi-line comments and tabs
        text = re.sub("/\*.*?\*/", "", text, flags = re.DOTALL).replace("\t", " ")
        #split text into lines, filtering empty lines, one-line comments, put
        #splits into line generator
        lines = (line.strip().split("//")[0].strip() for line in text.split("\n")\
         if line.strip() and not line.strip().startswith("//"))

        tokens, xml = [], "<tokens>\n"
        d = {"<": "&lt;",
             ">": "&gt;",
             "&": "&amp;"}

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

                    tokens.append((self.type(token), token))
                    xml += "<{type}> {token} </{type}> \n".format(\
                    token = d[token] if token in "<>&" else token.replace('"', ''),
                    type = self.type(token))

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

        return xml + "</tokens>\n", tokens

    def type(self, token):
        '''
        given token, return token type
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

class Txml(object):
    def __init__(self):
        self.Tokenizer = Tokenizer()

    def writeSingleFile(self, filename):
        '''
        write T.xml for a single file
        '''
        with open(filename, "r") as f:
            xml, _ = self.Tokenizer.tokenize(f.read())
            with open (os.path.basename(filename[:-5]) + "T.xml", "w") as o:
                o.write(xml)

    def write(self, path):
        '''
        write T.xml for input path regardless of path being a single file or a directory
        '''
        #path is a single file
        if path.endswith(".jack"):
            self.writeSingleFile(path)
        #path is a directory
        else:
            for filename in glob.glob(os.path.join(path, '*.jack')):
                self.writeSingleFile(filename)

if __name__ == "__main__":
    T = Txml()
    T.write(sys.argv[1])

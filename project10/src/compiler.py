import sys
import glob
import os
import tokenizer

class Compiler(object):
    def __init__(self, tokens):
        self.generator = ((type, token) for (type, token) in tokens)
        self.type, self.token = self.generator.next()

    def advance(self):
        try:
            self.type, self.token = self.generator.next()
        except StopIteration:
            pass

    def compileTerminal(self, word):
        xml = "<{type}> {token} </{type}>\n".format(type = self.type, token = self.token)
        self.advance()

        return xml

    def compileClass(self):
        xml = "<class>\n"
        xml += self.compileTerminal("class") + self.compileTerminal("className") +\
        self.compileTerminal("{") + self.compileClassVarDec() + \
        self.compileSubroutineDec() + self.compileTerminal("}")
        xml += "</class>\n"

        return xml

    def compileClassVarDec(self):
        if not self.token in {"static", "field"}:
            #There is no classVarDec
            return ""
        xml = "<classVarDec>\n"
        xml += self.compileTerminal("static|field") + self.compileTerminal("type") +\
        self.compileTerminal("varName")
        while self.token == ",":
            xml += self.compileTerminal(",") + self.compileTerminal("varName")
        xml += self.compileTerminal(";")
        xml += "</classVarDec>\n"
        xml += self.compileClassVarDec() #recursively compile multiple classVarDec

        return xml

    def compileSubroutineDec(self):
        #There is no subroutineDec
        if not self.token in {"constructor", "function", "method"}:
            return ""
        xml = "<subroutineDec>\n"
        xml += self.compileTerminal("constructor|function|method") +\
             self.compileTerminal("void|type") + self.compileTerminal("subroutineName") +\
             self.compileTerminal("(") + self.compileParameterList() + \
             self.compileTerminal(")") + self.compileSubroutineBody()
        xml += "</subroutineDec>\n"
        xml += self.compileSubroutineDec() # recursively compile multiple subroutineDec

        return xml

    def compileParameterList(self):
        xml = "<parameterList>\n"
        if self.token != ")":
            xml += self.compileTerminal("type") + self.compileTerminal("varName")
            while self.token == ",":
                xml += self.compileTerminal(",") + self.compileTerminal("type") + \
                self.compileTerminal("varName")
        xml += "</parameterList>\n"

        return xml

    def compileSubroutineBody(self):
        xml = "<subroutineBody>\n"
        xml += self.compileTerminal("{")
        while self.token == "var":
            xml += self.compileVarDec()
        xml += self.compileStatements() + self.compileTerminal("}")
        xml += "</subroutineBody>\n"

        return xml

    def compileVarDec(self):
        xml = "<varDec>\n"
        xml += self.compileTerminal("var") + self.compileTerminal("type") + \
            self.compileTerminal("varName")
        while self.token == ",":
            xml += self.compileTerminal(",") + self.compileTerminal("varName")
        xml += self.compileTerminal(";")
        xml += "</varDec>\n"

        return xml

    def compileStatements(self):
        #There are no statements
        if self.token not in {"let", "if", "while", "do", "return"}:
            return ""

        d = {"let": self.compileLet,
             "if": self.compileIf,
             "while": self.compileWhile,
             "do": self.compileDo,
             "return": self.compileReturn}

        xml = "<statements>\n"
        xml += d[self.token]()
        xml += "</statements>\n"

        return xml

    def compileLet(self):
        xml = "<letStatement>\n"
        xml += self.compileTerminal("let") + self.compileTerminal("varName")
        if self.token == "[":
            xml += self.compileTerminal("[") + self.compileTerminal("expression") +\
                self.compileTerminal("]")
        xml += self.compileTerminal("=") + self.compileExpression() +\
            self.compileTerminal(";") # "="
        xml += "</letStatement>\n"

        return xml

    def compileIf(self):
        xml += "<ifStatement>\n"
        xml += self.compileTerminal("if") + self.compileTerminal("(") +\
            self.compileExpression() + self.compileTerminal(")") +\
            self.compileTerminal("{") + self.compileStatements() +\
            self.compileTerminal("}")
        if self.token == "else":
            xml += self.compileTerminal("else") + self.compileTerminal("{")+\
                self.compileStatements() + self.compileTerminal("}")
        xml += "</ifStatement>\n"

        return xml

    def compileWhile(self):
        xml += "<whileStatement>\n"
        xml += self.compileTerminal("while") + self.compileTerminal("(") +\
            self.compileExpression() + self.compileTerminal(")") + \
            self.compileTerminal("{") + self.compileStatements() + \
            self.compileTerminal("}")
        xml += "</whileStatement>\n"

        return xml

    def compileDo(self):
        xml += "<doStatement>\n"
        xml += self.compileTerminal("do") + self.compileTerm() + \
            self.compileTerminal(";")
        xml += "</doStatement>\n"

        return xml

    def compileReturn(self):
        xml += "<returnStatement>\n"
        xml += self.compileTerminal("return")
        if self.token != ";":
            xml += self.compileExpression()
        xml += self.compileTerminal(";")
        xml += "</returnStatement>\n"

        return xml

    def compileExpression(self):
        xml = "<expression>\n"
        xml += self.compileTerm()
        while self.token in "+-*/&|<>=":
            xml += self.compileTerminal("op")
            xml += self.compileTerm()
        xml += "</expression>\n"

        return xml

    def compileTerm(self):
        xml = "<term>\n"
        if self.type in {"integerConstant", "stringConstant", "keyword", "identifier"}:
            xml += self.compileTerminal("integerConstant|stringConstant|keywordConstant|varName")
            if self.token == "[":
                xml += self.compileTerminal("[") + self.compileExpression() + \
                    self.compileTerminal("]")
            elif self.token == "(":
                xml += self.compileTerminal("(") + self.compileExpressionList() +\
                    self.compileTerminal(")")
            elif self.token == ".":
                xml += self.compileTerminal(".") + self.compileTerminal("subroutineName") +\
                    self.compileTerminal("(") + self.compileExpressionList() + \
                    self.compileTerminal(")")
        elif self.token == "(":
            xml += self.compileTerminal("(") + self.compileExpression() + \
                self.compileTerminal(")")
        elif self.token in "-~":
            xml += self.compileTerminal("unaryOp") + self.compileTerm()
        xml += "</term>\n"

        return xml

    def compileExpressionList(self):
        #expressionList is empty
        if self.token == ")":
            return ""
        xml = "<expressionList>\n"
        xml += self.compileExpression()
        while self.token == ",":
            xml += self.compileTerminal(",")
            xml += self.compileExpression()
        xml += "</expressionList>\n"

        return xml

class Xml(object):
    def __init__(self):
        self.Tokenizer = tokenizer.Tokenizer()

    def compileSingleFile(self, filename):
        '''
        write T.xml for a single file
        '''
        with open(filename, "r") as f:
            _, tokens = self.Tokenizer.tokenize(f.read())
            compiler = Compiler(tokens)
            xml = compiler.compileClass()
            with open (os.path.basename(filename[:-5]) + ".xml", "w") as o:
                o.write(xml)

    def compile(self, path):
        '''
        write T.xml for input path regardless of path being a single file or a directory
        '''
        #path is a single file
        if path.endswith(".jack"):
            self.compileSingleFile(path)
        #path is a directory
        else:
            for filename in glob.glob(os.path.join(path, '*.jack')):
                self.compileSingleFile(filename)

if __name__ == "__main__":
    X = Xml()
    X.compile(sys.argv[1])

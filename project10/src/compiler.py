import sys
import glob
import os
import tokenizer

class Compiler(object):
    #a parser that parses tokens into xml
    def __init__(self, tokens):
        '''
        Initialize a token generator generates pairs of (token_type, token)
        '''
        self.generator = ((type, token) for (type, token) in tokens)
        self.type, self.token = self.generator.next()

    def advance(self):
        '''
        Advances generator to generate new pairs of (token_type, token), stops
        when generator raises StopIteration, only called within compileTerminal()
        '''
        try:
            self.type, self.token = self.generator.next()
        except StopIteration:
            pass

    def compileTerminal(self, word = None):
        '''
        Compile terminal terms including keyword, symbol, integerConstant,
        stringConstant and identifier
        The argument word is not really passed to the function body, but is
        used as an annotation to show which terminal terms we are compiling
        for better readability
        It costs some extra memory to store the argument but it can be used, for
        example, for error tracking if we want to add functionality later on
        '''
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
            #when there is no classVarDec
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
        #when there is no subroutineDec
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
        #when parameterList is not empty
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
        #when there is varDec
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
        # #When there are no statements
        # if self.token not in {"let", "if", "while", "do", "return"}:
        #     return ""

        d = {"let": self.compileLet,
             "if": self.compileIf,
             "while": self.compileWhile,
             "do": self.compileDo,
             "return": self.compileReturn}

        xml = "<statements>\n"
        while self.token in d:
            xml += d[self.token]()
        xml += "</statements>\n"

        return xml

    def compileLet(self):
        xml = "<letStatement>\n"
        xml += self.compileTerminal("let") + self.compileTerminal("varName")
        if self.token == "[":
            xml += self.compileTerminal("[") + self.compileExpression() +\
                self.compileTerminal("]")
        xml += self.compileTerminal("=") + self.compileExpression() +\
            self.compileTerminal(";")
        xml += "</letStatement>\n"

        return xml

    def compileIf(self):
        xml = "<ifStatement>\n"
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
        xml = "<whileStatement>\n"
        xml += self.compileTerminal("while") + self.compileTerminal("(") +\
            self.compileExpression() + self.compileTerminal(")") + \
            self.compileTerminal("{") + self.compileStatements() + \
            self.compileTerminal("}")
        xml += "</whileStatement>\n"

        return xml

    def compileDo(self):
        xml = "<doStatement>\n"
        xml += self.compileTerminal("do") + self.compileTerm(True) + \
            self.compileTerminal(";")
        xml += "</doStatement>\n"

        return xml

    def compileReturn(self):
        xml = "<returnStatement>\n"
        xml += self.compileTerminal("return")
        if self.token != ";":
            xml += self.compileExpression()
        xml += self.compileTerminal(";")
        xml += "</returnStatement>\n"

        return xml

    def compileExpression(self):
        xml = "<expression>\n"
        xml += self.compileTerm()
        while self.token in {"+", "-", "*", "/", "&amp;", "|", "&lt;", "&gt;", "="}:
            xml += self.compileTerminal("op")
            xml += self.compileTerm()
        xml += "</expression>\n"

        return xml

    def compileTerm(self, isSubroutineCall = False):
        '''
        When isSubroutineCall is set to be True, subroutineCall is borrowing
        compileTerm function because the underline logic for compiling the two
        are the same, only except that there won't be wrapper <term> </term>
        when used for compiling subRoutineCall
        '''
        xml = ""
        if not isSubroutineCall:
            xml = "<term>\n"
        if self.type in {"integerConstant", "stringConstant", "keyword", "identifier"}:
            xml += self.compileTerminal("integerConstant|stringConstant|keywordConstant|varName")
            #including integerConstant|stringConstant|keywordConstant|varName
            #and the following specified cases
            if self.token == "[":
                #varName "[" expression "]"
                xml += self.compileTerminal("[") + self.compileExpression() + \
                    self.compileTerminal("]")
            elif self.token == "(":
                #subroutineName "(" expressionList ")"
                xml += self.compileTerminal("(") + self.compileExpressionList() +\
                    self.compileTerminal(")")
            elif self.token == ".":
                #(className|varName)"."subroutineName "(" expressionList ")"
                xml += self.compileTerminal(".") + self.compileTerminal("subroutineName") +\
                    self.compileTerminal("(") + self.compileExpressionList() + \
                    self.compileTerminal(")")
        elif self.token == "(":
            #"(" expression ")"
            xml += self.compileTerminal("(") + self.compileExpression() + \
                self.compileTerminal(")")
        elif self.token in "-~":
            #unaryOp term
            xml += self.compileTerminal("unaryOp") + self.compileTerm()
        if not isSubroutineCall:
            xml += "</term>\n"

        return xml

    def compileExpressionList(self):
        xml = "<expressionList>\n"
        if self.token != ")":
            #when there is at least one expression
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
            with open (filename[:-5] + ".xml", "w") as outf:
                outf.write(xml)

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

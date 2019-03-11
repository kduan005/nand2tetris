import sys
import glob
import os
import tokenizer
import symbolTable
import vmwriter

class CompileEngine(object):
    #a parser that parses tokens into xml
    def __init__(self, tokens):
        '''
        Initialize a token generator generates pairs of (token_type, token)
        '''
        self.generator = ((type, token) for (type, token) in tokens)
        self.type, self.token = self.generator.next()
        self.className = None
        self.subroutineName = None
        self.symbolTable = symbolTable.SymbolTable()
        self.vmwriter = vmwriter.Vmwriter()
        self.runningIdx = 0 #for creating unique labels for flow control

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

        # if self.type == "identifier":
        #     if self.token in self.symbolTable.subroutineTable or \
        #     self.token in self.symbolTable.classTable:
        #         xml = "<{type}> {kind} {varType} {index} {token} </{type}>\n".format(\
        #         type = self.type, token = self.token, \
        #         kind = self.symbolTable.kindOf(self.token), \
        #         varType = self.symbolTable.typeOf(self.token),
        #         index = self.symbolTable.indexOf(self.token))
        #     elif self.token == self.subroutineName:
        #         xml = "<{type}> subroutineName {token} </{type}>\n".format(\
        #         type = self.type, token = self.token)
        #     elif self.token == self.className:
        #         xml = "<{type}> className {token} </{type}>\n".format(\
        #         type = self.type, token = self.token)
        #     else:
        #         xml = "<{type}> {token} </{type}>\n".format(type = self.type, token = self.token)
        # else:
        #     xml = "<{type}> {token} </{type}>\n".format(type = self.type, token = self.token)

        self.advance()

        # return xml

    def compileClass(self):
        # xml = "<class>\n"
        self.compileTerminal("class")
        self.className = self.token
        self.compileTerminal("className")
        self.compileTerminal("{")
        self.compileClassVarDec()
        self.compileSubroutineDec()
        self.compileTerminal("}")
        # xml += "</class>\n"

        # return xml

    def compileClassVarDec(self):
        if not self.token in {"static", "field"}:
            #when there is no classVarDec
            return
        # xml = "<classVarDec>\n"
        kind = self.token
        self.compileTerminal("static|field")
        type = self.token
        self.compileTerminal("type")
        name = self.token
        self.symbolTable.define(name, type, kind)
        self.compileTerminal("varName")

        while self.token == ",":
            self.compileTerminal(",")
            name = self.token
            self.symbolTable.define(name, type, kind)
            self.compileTerminal("varName")
        self.compileTerminal(";")
        # xml += "</classVarDec>\n"
        self.compileClassVarDec() #recursively compile multiple classVarDec

        # return xml

    def compileSubroutineDec(self):
        #when there is no subroutineDec
        self.symbolTable.resetSubroutineTable()
        if not self.token in {"constructor", "function", "method"}:
            return
        # xml = "<subroutineDec>\n"
        funcType = self.token
        if funcType == "method":
            self.symbolTable.define("this", self.className, "argument")
        self.compileTerminal("constructor|function|method")

        returnType = self.token
        self.compileTerminal("void|type")

        subroutineName = self.className + "." + self.token
        self.compileTerminal("subroutineName")

        self.compileTerminal("(")
        self.compileParameterList()
        self.compileTerminal(")")

        self.compileSubroutineBody(funcType, returnType, subroutineName)
        # xml += "</subroutineDec>\n"
        self.compileSubroutineDec() # recursively compile multiple subroutineDec

        # return xml

    def compileParameterList(self):
        # xml = "<parameterList>\n"
        #when parameterList is not empty
        kind = "argument"
        if self.token != ")":
            type = self.token
            self.compileTerminal("type")
            varName = self.token
            self.symbolTable.define(varName, type, kind)
            self.compileTerminal("varName")
            while self.token == ",":
                self.compileTerminal(",")
                type = self.token
                self.compileTerminal("type")
                varName = self.token
                self.symbolTable.define(varName, type, kind)
                self.compileTerminal("varName")
        # xml += "</parameterList>\n"
        #
        # return xml

    def compileSubroutineBody(self, funcType, returnType, subroutineName):
        # xml = "<subroutineBody>\n"
        self.compileTerminal("{")
        #when there is varDec
        while self.token == "var":
            self.compileVarDec()

        self.vmwriter.writeFunction(subroutineName, self.symbolTable.varCount["local"])

        if funcType == "constructor":
            self.vmwriter.writePush("constant", self.symbolTable.varCount("field"))
            self.vmwriter.writeCall("Memory.alloc", 1)
            self.vmwriter.writePop("pointer", 0)
        elif funcType == "method":
            self.vmwriter.writePush("argument", 0)
            self.vmwriter.writePop("pointer", 0)

        self.compileStatements()
        self.compileTerminal("}")
        # xml += "</subroutineBody>\n"
        #
        # return xml

    def compileVarDec(self):
        # xml = "<varDec>\n"
        kind = "local"
        self.compileTerminal("var")
        type = self.token
        self.compileTerminal("type")
        varName = self.token
        self.symbolTable.define(varName, type, kind)
        self.compileTerminal("varName")
        while self.token == ",":
            self.compileTerminal(",")
            varName = self.token
            self.symbolTable.define(varName, type, kind)
            self.compileTerminal("varName")
        self.compileTerminal(";")
        # xml += "</varDec>\n"
        #
        # return xml

    def compileStatements(self):
        # #When there are no statements
        # if self.token not in {"let", "if", "while", "do", "return"}:
        #     return ""

        d = {"let": self.compileLet,
             "if": self.compileIf,
             "while": self.compileWhile,
             "do": self.compileDo,
             "return": self.compileReturn}

        # xml = "<statements>\n"
        while self.token in d:
            d[self.token]()
        # xml += "</statements>\n"
        #
        # return xml

    def compileLet(self):
        # xml = "<letStatement>\n"
        self.compileTerminal("let")
        varName = self.token
        self.compileTerminal("varName")
        if self.token == "[":
            #when manipulating array
            self.writePush(self.symbolTable.kindOf(varName), self.symbolTable.indexOf(varName))
            self.compileTerminal("[")
            self.compileExpression()
            self.vmwriter.writeArithmetic("add")
            self.compileTerminal("]")
            self.compileTerminal("=")
            self.compileExpression()
            self.vmwriter.writePop("temp", 0)
            self.vmwriter.writePop("pointer", 1)
            self.vmwriter.writePush("temp", 0)
            self.vmwriter.writePop("that", 0)
        else:
            self.compileTerminal("=")
            self.compileExpression()
            self.vmwriter.writePop(self.symbolTable.kindOf(varName), self.symbolTable.indexOf(varName))
        self.compileTerminal(";")

        # xml += "</letStatement>\n"
        #
        # return xml

    def compileIf(self):
        # xml = "<ifStatement>\n"
        self.compileTerminal("if")
        self.compileTerminal("(")
        self.compileExpression()
        self.compileTerminal(")")
        self.vmwriter.writeArithmetic("not")
        label1 = "label" + str(self.runningIdx)
        self.runningIdx += 1
        self.vmwriter.writeIf(label1)
        self.compileTerminal("{")
        self.compileStatements()
        self.compileTerminal("}")
        label2 = "label" + str(self.runningIdx)
        self.runningIdx += 1
        self.vmwriter.writeGoto(label2)
        self.vmwriter.writeLabel(label1)
        if self.token == "else":
            self.compileTerminal("else")
            self.compileTerminal("{")
            self.compileStatements()
            self.compileTerminal("}")
        self.vmwriter.writeLabel(label2)
        # xml += "</ifStatement>\n"
        #
        # return xml

    def compileWhile(self):
        xml = "<whileStatement>\n"
        xml += self.compileTerminal("while") + self.compileTerminal("(") +\
            self.compileExpression() + self.compileTerminal(")") + \
            self.compileTerminal("{") + self.compileStatements() + \
            self.compileTerminal("}")
        xml += "</whileStatement>\n"

        return xml

    def compileDo(self):
        # xml = "<doStatement>\n"
        self.compileTerminal("do")
        self.compileTerm(True)
        self.compileTerminal(";")
        self.vmwriter.writePop("temp", 0)
        # xml += "</doStatement>\n"
        #
        # return xml

    def compileReturn(self):
        # xml = "<returnStatement>\n"
        # if funcType == "constructor":
        #     self.vmwriter.writePush("pointer", 0)
        # if returnType == "void":
        #     self.vmwriter.writePush("constant", 0)
        self.vmwriter.writeReturn()
        self.compileTerminal("return")
        if self.token != ";":
            self.compileExpression()
        else:
            self.vmwriter.writePush("constant", 0)
        self.compileTerminal(";")
        # xml += "</returnStatement>\n"
        #
        # return xml

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

class Compiler(object):
    def __init__(self):
        self.Tokenizer = tokenizer.Tokenizer()

    def compileSingleFile(self, filename):
        '''
        write T.xml for a single file
        '''
        with open(filename, "r") as f:
            _, tokens = self.Tokenizer.tokenize(f.read())
            compileEngine = CompileEngine(tokens)
            xml = compileEngine.compileClass()
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
    X = Compiler()
    X.compile(sys.argv[1])

import symbolTable
import vmwriter

class CompileEngine(object):
    def __init__(self, tokens, filename):
        '''
        Initialize a token generator generates pairs of (token_type, token)
        '''
        self.generator = ((type, token) for (type, token) in tokens)
        self.type, self.token = self.generator.next()
        self.className = None
        self.subroutineName = None
        self.symbolTable = symbolTable.SymbolTable()
        self.vmwriter = vmwriter.Vmwriter(filename)
        #for creating unique labels for flow control
        self.runningIdx = 0

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
        self.advance()

    def compileClass(self):
        '''
        compiling class, the whole step for compiling any files
        '''
        self.compileTerminal("class")
        self.className = self.token
        self.compileTerminal("className")
        self.compileTerminal("{")
        self.compileClassVarDec()
        self.compileSubroutineDec()
        self.compileTerminal("}")

        self.vmwriter.close()

    def compileClassVarDec(self):
        if not self.token in {"static", "field"}:
            #when there is no classVarDec
            return

        #define variables in symbolTable
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

        #recursively compile multiple classVarDec
        self.compileClassVarDec()

    def compileSubroutineDec(self):
        #reset subroutine symbolTable to empty hashmap everytime when compiling a new subroutine
        self.symbolTable.resetSubroutineTable()
        #when there is no subroutineDec
        if not self.token in {"constructor", "function", "method"}:
            return

        #funcType: one of constructor|function|method
        funcType = self.token
        if funcType == "method":
            #if funcType is method, define this to be the first argument
            self.symbolTable.define("this", self.className, "argument")
        self.compileTerminal("constructor|function|method")

        #returnType: one of void|type
        returnType = self.token
        self.compileTerminal("void|type")

        #subroutineName: className.functionName
        subroutineName = self.className + "." + self.token
        self.compileTerminal("subroutineName")

        self.compileTerminal("(")
        self.compileParameterList()
        self.compileTerminal(")")

        self.compileSubroutineBody(funcType, returnType, subroutineName)

        # recursively compile multiple subroutineDec
        self.compileSubroutineDec()

    def compileParameterList(self):
        kind = "argument"
        #when parameterList is not empty, define each argument in symbolTable
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

    def compileSubroutineBody(self, funcType, returnType, subroutineName):
        self.compileTerminal("{")
        #when there is varDec
        while self.token == "var":
            self.compileVarDec()

        #function functionName nVar
        self.vmwriter.writeFunction(subroutineName, self.symbolTable.varCount("local"))

        if funcType == "constructor":
            #allocate memory address for constructor and push to pointer 0
            self.vmwriter.writePush("constant", self.symbolTable.varCount("field"))
            self.vmwriter.writeCall("Memory.alloc", 1)
            self.vmwriter.writePop("pointer", 0)
        elif funcType == "method":
            #push this to be pointer 0
            self.vmwriter.writePush("argument", 0)
            self.vmwriter.writePop("pointer", 0)

        self.compileStatements()
        self.compileTerminal("}")

    def compileVarDec(self):
        kind = "local"
        self.compileTerminal("var")
        type = self.token
        self.compileTerminal("type")
        varName = self.token
        #define local variables
        self.symbolTable.define(varName, type, kind)
        self.compileTerminal("varName")
        while self.token == ",":
            self.compileTerminal(",")
            varName = self.token
            self.symbolTable.define(varName, type, kind)
            self.compileTerminal("varName")
        self.compileTerminal(";")

    def compileStatements(self):
        d = {"let": self.compileLet,
             "if": self.compileIf,
             "while": self.compileWhile,
             "do": self.compileDo,
             "return": self.compileReturn}

        #compile different types of statements
        while self.token in d:
            d[self.token]()

    def compileLet(self):
        self.compileTerminal("let")
        varName = self.token
        self.compileTerminal("varName")
        if self.token == "[":
            #when manipulating array
            self.vmwriter.writePush(self.symbolTable.kindOf(varName), \
                self.symbolTable.indexOf(varName))
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
            #when assigning values to ordinary variables
            self.compileTerminal("=")
            self.compileExpression()
            self.vmwriter.writePop(self.symbolTable.kindOf(varName), \
                self.symbolTable.indexOf(varName))
        self.compileTerminal(";")

    def compileIf(self):
        self.compileTerminal("if")
        self.compileTerminal("(")
        self.compileExpression()
        self.compileTerminal(")")
        self.vmwriter.writeArithmetic("not")

        #label 1 when statement is true
        label1 = "label" + str(self.runningIdx)
        self.runningIdx += 1
        self.vmwriter.writeIf(label1)

        self.compileTerminal("{")
        self.compileStatements()
        self.compileTerminal("}")

        #label2 when else is true
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

    def compileWhile(self):
        self.compileTerminal("while")

        #label1 for when while statement is true
        label1 = "label" + str(self.runningIdx)
        self.runningIdx += 1
        self.vmwriter.writeLabel(label1)

        self.compileTerminal("(")
        self.compileExpression()
        self.compileTerminal(")")
        self.vmwriter.writeArithmetic("not")

        #label2 for when jumping out of loop
        label2 = "label" + str(self.runningIdx)
        self.runningIdx += 1
        self.vmwriter.writeIf(label2)

        self.compileTerminal("{")
        self.compileStatements()
        self.compileTerminal("}")

        self.vmwriter.writeGoto(label1)
        self.vmwriter.writeLabel(label2)

    def compileDo(self):
        self.compileTerminal("do")
        self.compileTerm()
        self.compileTerminal(";")
        #dump void return to temp 0
        self.vmwriter.writePop("temp", 0)

    def compileReturn(self):
        self.compileTerminal("return")
        if self.token != ";":
            #when return type is not void
            self.compileExpression()
        else:
            #when return type is void, return 0
            self.vmwriter.writePush("constant", 0)
        self.vmwriter.writeReturn()
        self.compileTerminal(";")

    def compileExpression(self):
        #transform infix expression to postfix on stack
        self.compileTerm()
        while self.token in {"+", "-", "*", "/", "&", "|", "<", ">", "="}:
            op = self.token
            self.compileTerminal("op")
            self.compileTerm()
            if op == "+":
                self.vmwriter.writeArithmetic("add")
            elif op == "-":
                self.vmwriter.writeArithmetic("sub")
            elif op == "*":
                self.vmwriter.writeCall("Math.multiply", 2)
            elif op == "/":
                self.vmwriter.writeCall("Math.divide", 2)
            elif op == "&":
                self.vmwriter.writeArithmetic("and")
            elif op == "|":
                self.vmwriter.writeArithmetic("or")
            elif op == "<":
                self.vmwriter.writeArithmetic("lt")
            elif op == ">":
                self.vmwriter.writeArithmetic("gt")
            elif op == "=":
                self.vmwriter.writeArithmetic("eq")

    def compileTerm(self):
        if self.type in {"integerConstant", "stringConstant", "keyword"}:
            # when current token is one of integerConstant|stringConstant|keyword
            if self.type == "integerConstant":
                self.vmwriter.writePush("constant", self.token)

            elif self.type == "stringConstant":
                self.vmwriter.writePush("constant", len(self.token))
                self.vmwriter.writeCall("String.new", 1)
                for ch in self.token:
                    self.vmwriter.writePush("constant", ord(ch))
                    self.vmwriter.writeCall("String.appendChar", 2)

            #when expressions are keywordConstants
            elif self.token == "this":
                self.vmwriter.writePush("pointer", 0)
            elif self.token in {"false", "null"}:
                self.vmwriter.writePush("constant", 0)
            elif self.token == "true":
                self.vmwriter.writePush("constant", 0)
                self.vmwriter.writeArithmetic("not")

            self.compileTerminal("integerConstant|stringConstant|keywordConstant")

        elif self.type == "identifier":
            identifier = self.token
            # when expressions are identifiers, it could be one of varName|varName'['expression']'|subRoutineCall
            self.compileTerminal("varName|subroutineName|className")

            if self.token == "[":
                #varName "[" expression "]"
                self.vmwriter.writePush(self.symbolTable.kindOf(identifier), \
                    self.symbolTable.indexOf(identifier))
                self.compileTerminal("[")
                self.compileExpression()
                self.compileTerminal("]")
                self.vmwriter.writeArithmetic("add")
                self.vmwriter.writePop("pointer", 1)
                self.vmwriter.writePush("that", 0)

            elif self.token == "(":
                #subroutineName "(" expressionList ")"
                #the function call must be a method within an outer method that
                #takes the object of his as both's first argument
                argNum = 1
                self.vmwriter.writePush("pointer", 0)
                fullSubName = self.className + "." + identifier
                self.compileTerminal("(")
                argNum += self.compileExpressionList()
                self.compileTerminal(")")
                self.vmwriter.writeCall(fullSubName, argNum)

            elif self.token == ".":
                #(className|varName)"."subroutineName "(" expressionList ")"
                argNum = 0
                self.compileTerminal(".")
                subroutineName = self.token
                self.compileTerminal("subroutineName")
                self.compileTerminal("(")
                if not self.symbolTable.typeOf(identifier):
                    #if identifier is not in symbolTable, it must be a className,
                    #and the function call must be a function instead of a method
                    fullSubName = identifier + "." + subroutineName
                else:
                    #if identifier is in symbolTable, it must be an varName,
                    #and the function call must be a method
                    #argNum plus one for including this
                    argNum = 1
                    # push this
                    self.vmwriter.writePush(self.symbolTable.kindOf(identifier),\
                        self.symbolTable.indexOf(identifier))
                    fullSubName = self.symbolTable.typeOf(identifier) + "." + \
                        subroutineName
                argNum += self.compileExpressionList()
                self.compileTerminal(")")
                self.vmwriter.writeCall(fullSubName, argNum)

            else:
                #varName
                self.vmwriter.writePush(self.symbolTable.kindOf(identifier), \
                    self.symbolTable.indexOf(identifier))

        elif self.token == "(":
            #"(" expression ")"
            self.compileTerminal("(")
            self.compileExpression()
            self.compileTerminal(")")

        elif self.token in "-~":
            #unaryOp term
            unaryOp = self.token
            self.compileTerminal("unaryOp")
            self.compileTerm()
            if unaryOp == "-":
                self.vmwriter.writeArithmetic("neg")
            elif unaryOp == "~":
                self.vmwriter.writeArithmetic("not")

    def compileExpressionList(self):
        #use argNum to record how many arguments in expressionList, to be returned
        argNum = 0
        if self.token != ")":
            #when there is at least one expression
            argNum += 1
            self.compileExpression()
            while self.token == ",":
                argNum += 1
                self.compileTerminal(",")
                self.compileExpression()

        return argNum

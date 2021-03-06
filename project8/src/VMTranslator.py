import sys
import collections
import glob
import os

class parser(object):
    '''
    parser class that parse a single line of vm command into individual parts
    including:
    commandType: if a command is arithmetic or push/pop
    argOne: first argument including "sub", "neg", "gt", "not",
    "add", "eq", "lt", "or", "and", "not", "push", "pop"
    argTwo: second argument, namely index into each memory segment, a command has
    second argument only when the command type is push/pop
    '''
    def __init__(self):
        #raw vm command
        self.raw = ""
        #split raw command into a list of tokens
        self.tokens = []
        self.commandType = ""
        self.argOne = ""
        self.argTwo = ""
        self.functionName = ""

    def genCommandType(self):
        #method to assign command type
        if self.tokens[0] in {"sub", "neg", "gt", "not", "add", "eq", "lt", "or",\
         "and", "not"}:
            self.commandType = "arithmetic"
        elif self.tokens[0] in {"push", "pop", "call", "function", "return", "bootstrap"}:
            self.commandType = self.tokens[0]
        elif self.tokens[0] in {"label", "goto", "if-goto"}:
            self.commandType = "branching"

    def genArgOne(self):
        #method to assign argOne according to command types
        if self.commandType in {"arithmetic", "branching"}:
            self.argOne = self.tokens[0]
        elif self.commandType in {"push", "pop", "call", "function"}:
            self.argOne = self.tokens[1]

    def genArgTwo(self):
        #method to assign argTwo, only applicable when command type is push/pop and branching
        if self.commandType in {"push", "pop", "call", "function"}:
            self.argTwo = self.tokens[2]
        elif self.commandType == "branching":
            self.argTwo = self.tokens[1]

    def genFunctionName(self):
        if self.commandType == "function":
            self.functionName = self.tokens[1]

    def generate(self, vmCmd):
        #generate commandType, argOne, argTwo for a single command line
        self.raw = vmCmd
        self.tokens = vmCmd.split(" ")
        self.genCommandType()
        self.genArgOne()
        self.genArgTwo()
        self.genFunctionName()

class codeWriter(object):
    '''
    codeWriter class to translate each vm command into assembly language command
    by using commandType, argOne, argTwo information associated with each command
    '''
    def __init__(self, outname):
        #take out filename from absolute/relative path and store it in self.outname
        #it will be used for generate label name for static variables
        self.outname = outname
        #commandType, argOne, argTwo attributes have the same value with those
        #associated with parser object
        self.commandType = ""
        self.argOne = ""
        self.argTwo = ""
        self.className = ""
        #a list for storing assembly language commands for each vm command line
        self.asmCmd = []
        #a counter for recording index of continue label in assembly language,
        #used for generating continue labels for vm command of "eq", "lt", "gt"
        self.counter = 0
        #output file
        self.outf = open(self.outname, "w")
        #a directory mapping key words in vm command to corresponding key words
        #in assembly language, default value set to be "self.outname.self.argTwo"
        #for mapping static variables and its labels
        self.d = {"temp0": "5",
                       "temp1": "6",
                       "temp2": "7",
                       "temp3": "8",
                       "temp4": "9",
                       "temp5": "10",
                       "temp6": "11",
                       "temp7": "12",
                       "pointer0": "3",
                       "pointer1": "4",
                       "local": "LCL",
                       "argument": "ARG",
                       "this": "THIS",
                       "that": "THAT",
                       "eq": "JEQ",
                       "lt": "JLT",
                       "gt": "JGT",
                       "add": "+",
                       "sub": "-",
                       "neg": "-",
                       "not": "!",
                       "and": "&",
                       "or": "|"}

    def writeCmd(self, parser):
        #set commandType, argOne, argTwo, functionName to be same with those of parser object
        self.commandType = parser.commandType
        self.argOne = parser.argOne
        self.argTwo = parser.argTwo
        self.functionName = parser.functionName
        #add raw command as comment at the top of block of assembly command
        #for debugging purpose
        self.asmCmd = ["// {}".format(parser.raw)]

        if self.commandType == "arithmetic":
            self.writeArithmetic()
        elif self.commandType == "push":
            self.writePush()
        elif self.commandType == "pop":
            self.writePop()
        elif self.commandType == "branching":
            self.writeBranching()
        elif self.commandType == "call":
            self.writeCall()
        elif self.commandType == "function":
            self.writeFunction()
        elif self.commandType == "return":
            self.writeReturn()
        elif self.commandType == "bootstrap":
            self.writeInit()

    def writeArithmetic(self):
        #method that calls different code generation methods according to
        #individual arithmetic type
        if self.argOne in {"add", "sub"}:
            self.add_sub()
        elif self.argOne in {"eq", "lt", "gt"}:
            self.eq_lt_gt()
        elif self.argOne in {"neg", "not"}:
            self.neg_not()
        elif self.argOne in {"and", "or"}:
            self.and_or()

    def add_sub(self):
        #generate asm code for "add" or "sub" command
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "A=A-1",
                            "M=M{}D".format(self.d[self.argOne])])

    def eq_lt_gt(self):
        #generate asm code for "eq", "lt" or "gt" command
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "A=A-1",
                            "D=M-D",
                            "M=-1",
                            "@CONTINUE{}".format(self.counter),
                            "D;{}".format(self.d[self.argOne]),
                            "@SP",
                            "A=M-1",
                            "M=0",
                            "(CONTINUE{})".format(self.counter)])
        #increment continue_counter by 1 for generating next continue label
        self.counter += 1

    def neg_not(self):
        #generate asm code for "neg" or "not" command
        self.asmCmd.extend(["@SP",
                            "A=M-1",
                            "M={}M".format(self.d[self.argOne])])

    def and_or(self):
        #generate asm code for "and" or "or" command
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "A=A-1",
                            "M=D{}M".format(self.d[self.argOne])])

    def writePush(self):
        #generate asm code for push command
        #case "constant"
        if self.argOne == "constant":
            self.asmCmd.extend(["@{}".format(self.argTwo),
                                "D=A",
                                "@SP",
                                "A=M",
                                "M=D",
                                "@SP",
                                "M=M+1"])
        #case "local", "argument", "this", "that"
        elif self.argOne in {"local", "argument", "this", "that"}:
            self.asmCmd.extend(["@{}".format(self.argTwo),
                                "D=A",
                                "@{}".format(self.d[self.argOne]),
                                "A=D+M",
                                "D=M",
                                "@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=D"])
        #case "temp", "pointer", "static"
        elif self.argOne in {"temp", "pointer", "static"}:
            self.asmCmd.extend(["@{}".format(self.className + self.argTwo \
                                if self.argOne == "static" \
                                else self.d[self.argOne + self.argTwo]),
                                "D=M",
                                "@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=D"])

    def writePop(self):
        #generate asm code for pop command
        #case "local", "argument", "this", "that"
        if self.argOne in {"local", "argument", "this", "that"}:
            self.asmCmd.extend(["@{}".format(self.argTwo),
                                "D=A",
                                "@{}".format(self.d[self.argOne]),
                                "M=D+M",
                                "@SP",
                                "AM=M-1",
                                "D=M",
                                "@{}".format(self.d[self.argOne]),
                                "A=M",
                                "M=D",
                                "@{}".format(self.argTwo),
                                "D=A",
                                "@{}".format(self.d[self.argOne]),
                                "M=M-D"])
        #case "temp", "pointer", "static"
        elif self.argOne in {"temp", "pointer", "static"}:
            self.asmCmd.extend(["@SP",
                                "AM=M-1",
                                "D=M",
                                "@{}".format(self.className + self.argTwo \
                                if self.argOne == "static" \
                                else self.d[self.argOne + self.argTwo]),
                                "M=D"])

    def writeBranching(self):
        #generate asm code for vm command with commandType "branching"
        if self.argOne == "label":
            self.label()
        elif self.argOne == "goto":
            self.goto()
        elif self.argOne == "if-goto":
            self.if_goto()

    def label(self):
        #generate asm code for "label label"
        self.asmCmd.extend(["({}${})".format(self.functionName, self.argTwo)])

    def goto(self):
        #generate asm code for "goto label"
        self.asmCmd.extend(["@{}${}".format(self.functionName, self.argTwo),
                            "0;JMP"])

    def if_goto(self):
        #generate asm code for "if-goto"
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "@{}${}".format(self.functionName, self.argTwo),
                            "D;JNE"])

    def writeCall(self):
        #generate asm code for "call function nArgs"
        self.asmCmd.extend(["//push returnAddr",
                            "@{}$ret.{}".format(self.functionName, self.counter),
                            "D=A",
                            "@SP",
                            "AM=M+1",
                            "A=A-1",
                            "M=D"])
        for key in ["LCL", "ARG", "THIS", "THAT"]:
            self.asmCmd.extend(["//push {}".format(key),
                                "@{}".format(key),
                                "D=M",
                                "@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=D"])
        self.asmCmd.extend(["//ARG = SP - 5 - n",
                            "@SP",
                            "D=M",
                            "@5",
                            "D=D-A",
                            "@{}".format(self.argTwo),
                            "D=D-A",
                            "@ARG",
                            "M=D",
                            "//LCL = SP",
                            "@SP",
                            "D=M",
                            "@LCL",
                            "M=D",
                            "//goto functionName",
                            "@{}".format(self.argOne),
                            "0;JMP",
                            "({}$ret.{})".format(self.functionName, self.counter)])
        self.counter += 1

    def writeFunction(self):
        #generate asm code for "function function nLcls"
        self.asmCmd.extend(["({})".format(self.functionName)])
        for i in range(int(self.argTwo)):
            self.asmCmd.extend(["@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=0"])

    def writeReturn(self):
        #generate asm code for "return"
        self.asmCmd.extend(["// endFrame = LCL",
                            "@LCL",
                            "D=M",
                            "@endFrame",
                            "M=D",
                            "// returnAddr = *(endFrame - 5)",
                            "@endFrame",
                            "D=M",
                            "@5",
                            "A=D-A",
                            "D=M",
                            "@returnAddr",
                            "M=D",
                            "// *ARG = pop()",
                            "@SP",
                            "A=M-1",
                            "D=M",
                            "@ARG",
                            "A=M",
                            "M=D",
                            "// SP = ARG + 1",
                            "@ARG",
                            "D=M+1",
                            "@SP",
                            "M=D"])
        for i, key in enumerate(["THAT", "THIS", "ARG", "LCL"]):
            self.asmCmd.extend(["//{} = *(endFrame-{})".format(key, i+1),
                                "@endFrame",
                                "D=M",
                                "@{}".format(i+1),
                                "A=D-A",
                                "D=M",
                                "@{}".format(key),
                                "M=D"])
        self.asmCmd.extend(["//goto returnAddr",
                            "@returnAddr",
                            "A=M",
                            "0;JMP"])

    def writeInit(self):
        #generate asm code for "bootstrap"
        self.asmCmd.extend(["@256",
                            "D=A",
                            "@SP",
                            "M=D"])

    def close(self):
        #close output file
        self.outf.close()

class vmTranslator(object):
    #vmTranslator class pieces parser and codeWriter together, constructor takes
    #the file path and file name to be translated, constructs parser and codeWriter
    def __init__(self, path):
        self.path = path
        #setting self.outname to be the name of output file
        if path[-3:] == ".vm":
            self.outname = path[:-3] + ".asm"
        else:
            self.outname = path + "/" + path.split("/")[-1] + ".asm"
        #construct parser and codeWriter
        self.parser = parser()
        self.codeWriter = codeWriter(self.outname)
        #adding bootstrap code
        for raw in ["bootstrap", "call Sys.init 0"]:
            #translate vm command into assembly command
            self.parser.generate(raw)
            self.codeWriter.writeCmd(self.parser)
            #write assembly command into output file
            for cmd in self.codeWriter.asmCmd:
                self.codeWriter.outf.write(cmd + "\n")

    def TranslateSingleFile(self, inputName):
        #method to translate a single file when there are multiple .vm in a directory
        try:
            inf = open(inputName, "r")
        except:
            print("File not found or path is incorrect")
        else:
            with inf:
                for row in inf:
                    #skip if the input line is comment or empty line
                    if row[:2] == "//" or row == "\r\n":
                        continue
                    #translate vm command into assembly command
                    self.parser.generate(row.replace("\r\n", ""))
                    self.codeWriter.writeCmd(self.parser)
                    #write assembly commands into output file
                    for cmd in self.codeWriter.asmCmd:
                        self.codeWriter.outf.write(cmd + "\n")

    def Translator(self):
        #translate a single file or all .vm files within a directory
        #when translating a single file
        if self.path[-3:] == ".vm":
            #update className associated with a file
            self.codeWriter.className = self.path.split("/")[-1][:-3]
            self.TranslateSingleFile(self.path)
        #when translating multiple .vm files within a directory
        else:
            for filename in glob.glob(os.path.join(self.path, '*.vm')):
                #for each file, update the className associate with each
                self.codeWriter.className = filename.split("/")[-1][:-3]
                self.TranslateSingleFile(filename)

        self.codeWriter.close()

if __name__ == "__main__":
    vt = vmTranslator(sys.argv[1])
    vt.Translator()

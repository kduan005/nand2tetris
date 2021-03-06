import sys
import collections

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

    def genCommandType(self):
        #method to assign command type
        if self.tokens[0] in {"sub", "neg", "gt", "not", "add", "eq", "lt", "or",\
         "and", "not"}:
            self.commandType = "arithmetic"
        else:
            #push/pop
            self.commandType = self.tokens[0]

    def genArgOne(self):
        #method to assign argOne according to command types
        if self.commandType == "arithmetic":
            self.argOne = self.tokens[0]
        else:
            self.argOne = self.tokens[1]

    def genArgTwo(self):
        #method to assign argTwo, only applicable when command type is push/pop
        if self.commandType in {"push", "pop"}:
            self.argTwo = self.tokens[2]

    def generate(self, vmCmd):
        #generate commandType, argOne, argTwo for a single command line
        self.raw = vmCmd
        self.tokens = vmCmd.split(" ")
        self.genCommandType()
        self.genArgOne()
        self.genArgTwo()

class codeWriter(object):
    '''
    codeWriter class to translate each vm command into assembly language command
    by using commandType, argOne, argTwo information associated with each command
    '''
    def __init__(self, outname):
        #take out filename from absolute/relative path and store it in self.outname
        #it will be used for generate label name for static variables
        self.outname = outname.split("/")[-1]
        #commandType, argOne, argTwo attributes have the same value with those
        #associated with parser object
        self.commandType = ""
        self.argOne = ""
        self.argTwo = ""
        #a list for storing assembly language commands for each vm command line
        self.asmCmd = []
        #a counter for recording index of continue label in assembly language,
        #used for generating continue labels for vm command of "eq", "lt", "gt"
        self.continue_counter = 0
        #output file
        self.outf = open(outname + ".asm", "w")
        #a directory mapping key words in vm command to corresponding key words
        #in assembly language, default value set to be "self.outname.self.argTwo"
        #for mapping static variables and its labels
        self.d = collections.defaultdict(lambda: self.outname + "." + self.argTwo)
        self.d.update({"temp0": "5",
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
                       "or": "|"})

    def writeCmd(self, parser):
        #set commandType, argOne, argTwo to be same with those of parser object
        self.commandType = parser.commandType
        self.argOne = parser.argOne
        self.argTwo = parser.argTwo
        #add raw command as comment at the top of block of assembly command
        #for debugging purpose
        self.asmCmd = ["// " + parser.raw]

        if self.commandType == "arithmetic":
            self.writeArithmetic()
        elif self.commandType == "push":
            self.writePush()
        elif self.commandType == "pop":
            self.writePop()

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

    def writePush(self):
        #generate asm code for push command
        #case "constant"
        if self.argOne == "constant":
            self.asmCmd.extend(["@" + self.argTwo,
                                "D=A",
                                "@SP",
                                "A=M",
                                "M=D",
                                "@SP",
                                "M=M+1"])
        #case "local", "argument", "this", "that"
        elif self.argOne in {"local", "argument", "this", "that"}:
            self.asmCmd.extend(["@" + self.argTwo,
                                "D=A",
                                "@" + self.d[self.argOne],
                                "AM=D+M",
                                "D=M",
                                "@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=D",
                                "@" + self.argTwo,
                                "D=A",
                                "@" + self.d[self.argOne],
                                "M=M-D"])
        #case "temp", "pointer", "static"
        elif self.argOne in {"temp", "pointer", "static"}:
            self.asmCmd.extend(["@" + self.d[self.argOne + self.argTwo],
                                "D=M",
                                "@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=D"])

    def writePop(self):
        #generate asm code for pop command
        #case "local", "argument", "this", "that"
        if self.argOne in {"local", "argument", "this", "that"}:
            self.asmCmd.extend(["@" + self.argTwo,
                                "D=A",
                                "@" + self.d[self.argOne],
                                "M=D+M",
                                "@SP",
                                "AM=M-1",
                                "D=M",
                                "@" + self.d[self.argOne],
                                "A=M",
                                "M=D",
                                "@" + self.argTwo,
                                "D=A",
                                "@" + self.d[self.argOne],
                                "M=M-D"])
        #case "temp", "pointer", "static"
        elif self.argOne in {"temp", "pointer", "static"}:
            self.asmCmd.extend(["@SP",
                                "AM=M-1",
                                "D=M",
                                "@" + self.d[self.argOne + self.argTwo],
                                "M=D"])

    def add_sub(self):
        #generate asm code for "add" or "sub" command
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "A=A-1",
                            "M=M" + self.d[self.argOne] + "D"])

    def eq_lt_gt(self):
        #generate asm code for "eq", "lt" or "gt" command
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "A=A-1",
                            "D=M-D",
                            "M=-1",
                            "@CONTINUE" + str(self.continue_counter),
                            "D;" + self.d[self.argOne],
                            "@SP",
                            "A=M-1",
                            "M=0",
                            "(CONTINUE" + str(self.continue_counter) + ")"])
        #increment continue_counter by 1 for generating next continue label
        self.continue_counter += 1

    def neg_not(self):
        #generate asm code for "neg" or "not" command
        self.asmCmd.extend(["@SP",
                            "A=M-1",
                            "M=" + self.d[self.argOne] + "M"])

    def and_or(self):
        #generate asm code for "and" or "or" command
        self.asmCmd.extend(["@SP",
                            "AM=M-1",
                            "D=M",
                            "A=A-1",
                            "D=D" + self.d[self.argOne] + "M",
                            "M=D"])

    def close(self):
        #close output file
        self.outf.close()

class vmTranslator(object):
    #vmTranslator class pieces parser and codeWriter together, constructor takes
    #the file path and file name to be translated, constructs parser and codeWriter
    def __init__(self, inputName):
        self.inputName = inputName
        self.parser = parser()
        self.codeWriter = codeWriter(self.inputName[:-3])

    def Translator(self):
        try:
            inf = open(self.inputName, "r")
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
            self.codeWriter.close()

if __name__ == "__main__":
    vt = vmTranslator(sys.argv[1])
    vt.Translator()

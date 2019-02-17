import sys
import collections

class parser(object):
    '''
    parser class that translate a single line of vm command into asm command
    '''
    def __init__(self):
        self.raw = "" #raw vm command
        self.tokens = [] #split raw command into tokens
        self.commandType = ""
        self.argOne = ""
        self.argTwo = ""

    def genCommandType(self):
        if self.tokens[0] in {"sub", "neg", "gt", "not", "add", "eq", "lt", "or", "and", "not"}:
            self.commandType = "ari"
        else:
            self.commandType = self.tokens[0]

    def genArgOne(self):
        if self.commandType == "ari":
            self.argOne = self.tokens[0]
        else:
            self.argOne = self.tokens[1]

    def genArgTwo(self):
        if self.commandType in {"push", "pop"}:
            self.argTwo = self.tokens[2]

    def generate(self, vmCmd):
        self.raw = vmCmd
        self.tokens = vmCmd.split(" ")
        self.genCommandType()
        self.genArgOne()
        self.genArgTwo()

class codeWriter(object):
    '''
    codeWriter class to translate each vm
    '''
    def __init__(self, outname):
        self.outname = outname.split("/")[-1]
        self.commandType = ""
        self.argOne = ""
        self.argTwo = ""
        self.asmCmd = []
        self.continue_counter = 0
        self.outf = open(outname + ".asm", "w")
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
        self.commandType = parser.commandType
        self.argOne = parser.argOne
        self.argTwo = parser.argTwo
        self.asmCmd = ["// " + parser.raw]

        if self.commandType == "ari":
            self.writeArithmetic()
        elif self.commandType == "push":
            self.writePush()
        elif self.commandType == "pop":
            self.writePop()

    def writeArithmetic(self):
        #method that will call different code generation methods according to
        #arithmetic type
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
        #case constant
        if self.argOne == "constant":
            self.asmCmd.extend(["@" + self.argTwo,
                                "D=A",
                                "@SP",
                                "A=M",
                                "M=D",
                                "@SP",
                                "M=M+1"])

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

        elif self.argOne in {"temp", "pointer", "static"}:
            self.asmCmd.extend(["@" + self.d[self.argOne + self.argTwo],
                                "D=M",
                                "@SP",
                                "AM=M+1",
                                "A=A-1",
                                "M=D"])

    def writePop(self):
        #generate asm code for pop command
        #case "local" or "argument"
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

        elif self.argOne in {"temp", "pointer", "static"}:
            self.asmCmd.extend(["@SP",
                                "AM=M-1",
                                "D=M",
                                "@" + self.d[self.argOne + self.argTwo],
                                "M=D"])

    def add_sub(self):
        #generate asm code for add or sub command
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
        self.outf.close()

class vmTranslator(object):

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
                    if row[:2] == "//" or row == "\r\n":
                        continue
                    self.parser.generate(row.replace("\r\n", ""))
                    self.codeWriter.writeCmd(self.parser)
                    for cmd in self.codeWriter.asmCmd:
                        self.codeWriter.outf.write(cmd + "\n")
            self.codeWriter.close()

if __name__ == "__main__":
    vt = vmTranslator(sys.argv[1])
    vt.Translator()

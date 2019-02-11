import sys

class textClean(object):
    def __init__(self):
        self.output = []

    def textClean(self, inname):
        '''
        Function to execute text cleaning
        Input: str, name of file for text cleaning, "<filename>.in"
        The function will create an output file named "<filename>.out"
        in the directory where <filename>.in resides
        '''
        #reference https://stackoverflow.com/questions/713794/catching-an-exception-while-using-a-python-with-statement
        try:
            inf = open(inname, "r")
        except:
            print("File not found or path is incorrect")
        else:
            skipflag = False

            with inf:
                for row in inf:
                    clean = self.stripSpacesTabs(row)
                    clean = self.stripSingleLineComments(clean)

                    if not clean:
                        continue

                    if self.isBlockCommentsStart(clean):
                        #In case multi-line comments start mid-line, keep what's before
                        clean = self.removeStartingComments(clean)
                        if clean:
                            self.output.append(clean)
                        skipflag = True

                    if not skipflag:
                        self.output.append(clean)

                    if self.isBlockCommentsEnd(row):
                        #In case multi-line comments end mid-line, keep what's after
                        clean = self.removeClosingComments(clean)
                        if clean:
                            self.output.append(clean)
                        skipflag = False

        return self.output

    def stripSpacesTabs(self, s):
        '''
        Function to remove all white spaces, tab and line returns(to be added
        back again at the end) in a row of string
        Input: str containing white spaces
        Output: str after removing white spaces
        '''
        for ch in (" ", "\t", "\n", "\r"):
            s = s.replace(ch, "")
        return s

    def stripSingleLineComments(self, s):
        '''
        Function to remove a single line of comments starting with //
        Input: str containing comments
        Output: str after removing comments
        '''
        for i in range(len(s)-1):
            if s[i:i+2] == "//":
                return s[:i]
        return s

    def isBlockCommentsStart(self, s):
        '''
        Input: str to examine
        Output: Bool, true if /* is in the str otherwise false
        '''
        return True if "/*" in s else False

    def removeStartingComments(self, s):
        '''
        Removing comments with leading "/*" from a line
        Input: str containing comments
        Output: str after removing start of multi-lines comments
        '''
        for i in range(len(s)-1):
            if s[i:i+2] == "/*":
                return s[:i]

    def isBlockCommentsEnd(self, s):
        '''
        Input: str to examine
        Output: Bool, true if */ is in the str otherwise false
        '''
        return self.isBlockCommentsStart(s[::-1])

    def removeClosingComments(self, s):
        '''
        Removing comments with closing "*/" from a line
        Input: str containing comments
        Ouput: str after striping
        '''
        for i in range(1, len(s)):
            if s[i-1:i+1] == "*/":
                return s[i+1:]

class assembler(object):
    def __init__(self, input):
        #clean syntax after processed by textClean
        self.input = input
        #contain resulting syntax of firstPass processing
        self.firstPassOutput = []
        #machine language translated by assembler
        self.output = []
        #directory containing mappings of symbols to locations/addresses
        self.symbolTable = {"SP": 0,
                            "LCL": 1,
                            "ARG": 2,
                            "THIS": 3,
                            "THAT": 4,
                            "R0": 0,
                            "R1": 1,
                            "R2": 2,
                            "R3": 3,
                            "R4": 4,
                            "R5": 5,
                            "R6": 6,
                            "R7": 7,
                            "R8": 8,
                            "R9": 9,
                            "R10": 10,
                            "R11": 11,
                            "R12": 12,
                            "R13": 13,
                            "R14": 14,
                            "R15": 15,
                            "SCREEN": 16384,
                            "KBD": 24576}
        #addresses for symbol assignments, starting from 16
        self.ramAdd = 16
        #compTable mapping comp part in C instruction to its corresponding
        #binary bits from c1-c6
        self.compTable = {"0": "101010",
                          "1": "111111",
                          "-1": "111010",
                          "D": "001100",
                          "A": "110000",
                          "M": "110000",
                          "!D": "001101",
                          "!A": "110001",
                          "!M": "110001",
                          "-D": "001111",
                          "-A": "110011",
                          "-M": "110011",
                          "D+1": "011111",
                          "A+1": "110111",
                          "M+1": "110111",
                          "D-1": "001110",
                          "A-1": "110010",
                          "M-1": "110010",
                          "D+A": "000010",
                          "D+M": "000010",
                          "D-A": "010011",
                          "D-M": "010011",
                          "A-D": "000111",
                          "M-D": "000111",
                          "D&A": "000000",
                          "D&M": "000000",
                          "D|A": "010101",
                          "D|M": "010101"}
        #destTable mapping dest part in C instruction to its corresponding
        #binary bits from d1-d3
        self.destTable = {"M": "001",
                          "D": "010",
                          "DM": "011",
                          "A": "100",
                          "AM": "101",
                          "AD": "110",
                          "ADM": "111"}
        #jumpTable mapping jump part in C instruction to its corresponding
        #binary bits from j1-j3
        self.jumpTable = {"JGT": "001",
                          "JEQ": "010",
                          "JGE": "011",
                          "JLT": "100",
                          "JNE": "101",
                          "JLE": "110",
                          "JMP": "111"}

    def firstPass(self):
        '''
        First pass of assembler, taking in cleaned syntaxes processed by textClean;
        adding syntaxes after taking out labels to self.firstPassOutput
        and assign labels to line numbers at the meantime
        '''
        for syntax in self.input:
            #striping parenthesis wrap of labels, assign address to symbol
            if syntax[0] == "(":
                for ch in ("(", ")"):
                    syntax = syntax.replace(ch, "")
                self.symbolTable[syntax] = len(self.firstPassOutput)
            else:
                self.firstPassOutput.append(syntax)

    def secondPass(self):
        '''
        Second pass, translate assembly language to machine language
        '''
        for syntax in self.firstPassOutput:
            #case @counter, assign address to symbol "counter",
            #increment self.ramAdd by 1
            if syntax[0] == "@" and not syntax[1].isdigit():
                symbol = syntax[1:]
                if symbol not in self.symbolTable:
                    self.symbolTable[symbol] = self.ramAdd
                    self.ramAdd += 1

            self.output.append(self.asmToMl(syntax))

    def asmToMl(self, syntax):
        '''
        Translate every assembly syntax into machine language syntax
        '''
        #case A instruction
        if syntax[0] == "@":
            value = syntax[1:]
            #if value after @ is not numeric but a symbol, look up in symbolTable
            if not value[0].isdigit():
                value = self.symbolTable[value]
            return "{0:016b}".format(int(value))
        #case C instruction
        else:
            bi_a, bi_c1Toc6, bi_d1Tod3, bi_j1Toj3 = "0", "0" * 6, "0" * 3, "0" * 3
            comp = syntax
            dest = jump = None
            #case when dest exists, slice comp into dest and comp
            if "=" in comp:
                i = comp.index("=")
                comp, dest = comp[i+1:], comp[:i]
            #case when jump exists, slice comp into comp and jump
            if ";" in comp:
                j = comp.index(";")
                comp, jump = comp[:j], comp[j+1:]
            #bit a should be 1 when M is in comp otherwise 0
            if "M" in comp:
                bi_a = "1"
            #bit c1-c6
            bi_c1Toc6 = self.compTable[comp]
            #bit d1-d3
            if dest:
                bi_d1Tod3 = self.destTable["".join(sorted(dest))]
            #bit j1-j3
            if jump:
                bi_j1Toj3 = self.jumpTable[jump]

            return "111" + bi_a + bi_c1Toc6 + bi_d1Tod3 + bi_j1Toj3

    def toBinary(self, outname):
        self.firstPass()
        self.secondPass()
        outf = open(outname, "w")
        with outf:
            for row in self.output:
                row += "\n"
                outf.write(row)

if __name__ == '__main__':
    t = textClean()
    inname = sys.argv[1]
    outname = inname.split(".")[0] + ".hack"
    text = t.textClean(inname)
    a = assembler(text)
    a.toBinary(outname)

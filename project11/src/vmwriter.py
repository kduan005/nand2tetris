class Vmwriter(object):
    '''
    Vmwrite opens the output file path and write vm code compiled by the
    compileEngine into the output file
    '''
    def __init__(self, filename):
        self.f = open(filename, "w")

    def writePush(self, segment, index):
        if segment == "field":
            segment = "this"
        self.f.write("push {} {}\n".format(segment, index))

    def writePop(self, segment, index):
        if segment == "field":
            segment = "this"
        self.f.write("pop {} {}\n".format(segment, index))

    def writeArithmetic(self, arithmetic):
        self.f.write(arithmetic + "\n")

    def writeLabel(self, label):
        self.f.write("label {}\n".format(label))

    def writeGoto(self, label):
        self.f.write("goto {}\n".format(label))

    def writeIf(self, label):
        self.f.write("if-goto {}\n".format(label))

    def writeCall(self, functionName, argumentNumber):
        self.f.write("call {} {}\n".format(functionName, argumentNumber))

    def writeFunction(self, functionName, varNumber):
        self.f.write("function {} {}\n".format(functionName, varNumber))

    def writeReturn(self):
        self.f.write("return\n")

    def close(self):
        self.f.close()

class Vmwriter(object):
    def __init__(self, filename):
        self.f = open(filename, "w")

    def writePush(self, segment, index):
        self.f.write("push {} {}\n".format(segment, index))

    def writePop(self, segment, index):
        self.f.write("pop {} {}\n".format(segment, index))

    def writeArithmetic(self, arithmetic):
        self.f.write(arithmetic + "\n")

    def writeLabel(self, label):
        self.f.write("({})\n".format(label))

    def writeGoto(self, label):
        self.f.write("goto {}\n".format(label))

    def writeIf(self, label):
        self.f.write("if-goto {}\n".format(label))

    def writeCall(self, functionName, argumentNumber):
        self.f.write("call {} {}\n".format(functionName, argumentNumber))

    def writeFunction(self, functionName, varNumber):
        self.f.write("{} {}\n".format(functionName, varNumber))

    def writeReturn(self):
        self.f.write("return\n")

    def close(self):
        self.f.close()

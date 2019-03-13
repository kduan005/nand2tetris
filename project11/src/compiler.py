import sys
import glob
import os
import tokenizer
import compileEngine

class Compiler(object):
    def __init__(self):
        self.Tokenizer = tokenizer.Tokenizer()

    def compileSingleFile(self, filename):
        '''
        Compile a single file
        '''
        with open(filename, "r") as f:
            CE = compileEngine.CompileEngine(self.Tokenizer.tokenize(f.read()), \
            filename[:-5] + ".vm")
            CE.compileClass()

    def compile(self, path):
        '''
        Compile for input path
        If input pass is a directory, compile every .jack file in the directory
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

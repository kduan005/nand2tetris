import sys

def textClean(inname):
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
        outname = inname[:-3] + ".out"
        outf = open(outname, "w")
        skipflag = False
        with inf, outf:
            for row in inf:
                clean = stripSpacesTabs(row)
                clean = stripSingleLineComments(clean)
                if clean == "\n":
                    continue
                if isBlockCommentsStart(clean):
                    skipflag = True
                if not skipflag:
                    outf.write(str(clean))
                if isBlockCommentsEnd(row):
                    skipflag = False

def stripSpacesTabs(s):
    '''
    Function to remove all white spaces in a row of string
    Input: str containing white spaces
    Output: str after removing white spaces
    '''
    s = s.replace(" ", "")
    s = s.replace("\t", "")
    return s

def stripSingleLineComments(s):
    '''
    Function to remove a single line of comments starting with //
    Input: str containing comments
    Output: str after removing comments
    '''
    for i in range(len(s)-1):
        if s[i:i+2] == "//":
            return s[:i] + "\n"
    return s

def isBlockCommentsStart(s):
    '''
    Input: str to examine
    Output: Bool, true if /* is in the str otherwise false
    '''
    return True if "/*" in s else False

def isBlockCommentsEnd(s):
    '''
    Input: str to examine
    Output: Bool, true if */ is in the str otherwise false
    '''
    return isBlockCommentsStart(s[::-1])

if __name__ == '__main__':
    textClean(sys.argv[1])

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
                    #In case multi-line comments start mid-line, keep what's before
                    clean = removeStartingComments(clean)
                    if clean != "\n":
                        outf.write(str(clean))
                    skipflag = True

                if not skipflag:
                    outf.write(str(clean))

                if isBlockCommentsEnd(row):
                    #In case multi-line comments end mid-line, keep what's after
                    clean = removeClosingComments(clean)
                    if clean != "\n":
                        outf.write(str(clean))
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

def removeStartingComments(s):
    '''
    Removing comments with leading "/*" from a line
    Input: str containing comments
    Output: str after removing start of multi-lines comments
    '''
    for i in range(len(s)-1):
        if s[i:i+2] == "/*":
            return s[:i] + "\n"

def isBlockCommentsEnd(s):
    '''
    Input: str to examine
    Output: Bool, true if */ is in the str otherwise false
    '''
    return isBlockCommentsStart(s[::-1])

def removeClosingComments(s):
    '''
    Removing comments with closing "*/" from a line
    Input: str containing comments
    Ouput: str after striping
    '''
    for i in range(1, len(s)):
        if s[i-1:i+1] == "*/":
            return s[i+1:]

if __name__ == '__main__':
    textClean(sys.argv[1])

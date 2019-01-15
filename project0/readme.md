Usage instruction for cleantext.py

In shell command, append the absolute/relative path of your ".in" file that you
want to clean in the format of string after textclean.py as follows:

$ python textclean.py '../test.in'

$ python textclean.py '/Users/kduan/Documents/Intro_to_Computer_System/nand2tetris/project0/test.in'

After execute the command line, you should be able to see a ".out" file with
the same name of your input file reside in the same directory with the input file.

The program will:
1)Remove all white space from <filename>.in, including spaces, tabs, and blank lines,
but not line returns;
2)Remove all comments in addition to the whitespace. Comments come in two forms:
- comments begin with the sequence "//" and end at the line return
- comments begin with the sequence /* and end at the sequence */

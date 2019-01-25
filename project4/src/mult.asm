// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)

    @0
    D = A         //initialize R2 to be 0
    @R2
    M = D
(LOOP)
    @R2
    M = M + D     //increment R2 by R0
    @R1
    D = M
    M = M - 1     //decrease R1 by 1, and jump out of loop if R1 is 0 before decreasing
    @END
    D; JEQ
    @R0           //re-register D with value of R0
    D = M
    @LOOP
    0; JMP

(END)
    @END
    0; JMP

// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed.
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

    @1
    D = A         //distance variable standing for the current pixel's
    @distance     //distance from the start(RAM[16384]), initialized to 1 to offset
    M = D         //the first step-back after loading the first iteration

(LOOP)
    @KBD          //check if KBD = 0, if so jump to CLEAN
    D = M
    @CLEAN
    D; JEQ

(FILL)
    @distance
    D = M
    @SCREEN       //executing blackening pixels, add distance to SCREEN address to
    A = D + A     //calculate current address
    M = -1
    @distance
    MD = M + 1    //increment distance by 1, move on to next pixel
    @8192         //check if pixel reaches maximum address(24575), if so
    D = D - A     //jump to HOLDUPPER and pixel address will be held at 24575
    @HOLDUPPER
    D; JEQ
    @LOOP
    0; JMP        //if address within bound, jump back to beginnng address

(CLEAN)
    @distance     //write off blackened pixel by one step back, decrease address
    M = M - 1     //first and then change storage in memory back to 0
    D = M
    @SCREEN
    A = D + A
    M = 0
    @HOLDLOWER    //check if address is already backed to start(16384), if so
    D; JEQ        //jump to HOLDLOWER to keep address at 0
    @LOOP
    0; JMP

(HOLDUPPER)
    @KBD          //when staying at maximum, check if keyboard is pressed, if so
    D = M         //jump out of holding loop
    @LOOP
    D; JEQ
    @HOLDUPPER
    0; JMP

(HOLDLOWER)
    @KBD          //when staying at minimum, check if keyboard is released, if so
    D = M         //jump out of holding loop
    @LOOP
    D; JGT
    @HOLDLOWER
    0; JMP

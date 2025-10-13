//==============================================================
// File: nand.sv
// Description: Basic NAND gate implementation in SystemVerilog
//
// This module performs the NAND (NOT-AND) operation.
//
// A NAND gate outputs logic 0 only when *both* inputs are logic 1.
// Otherwise, it outputs logic 1.
//
//--------------------------------------------------------------
// TRUTH TABLE for NAND Gate
// -------------------------------------------------------------
// | inA | inB | outY = ~(inA & inB) |
// |------|------|---------------------|
// |  0   |  0   |          1          |
// |  0   |  1   |          1          |
// |  1   |  0   |          1          |
// |  1   |  1   |          0          |
// -------------------------------------------------------------
//
// In Boolean algebra: outY = NOT (inA AND inB)
//==============================================================

module myNAND (
    input  logic inA,   // Input A
    input  logic inB,   // Input B
    output logic outY   // Output Y (NAND result)
);

    // Perform NAND operation:
    // '&' performs logical AND
    // '~' performs bitwise NOT (inversion)
    assign outY = ~(inA & inB);

endmodule

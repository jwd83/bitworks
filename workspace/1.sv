//==============================================================
// Description: NOT gate implemented *using* a NAND gate
//
// This module demonstrates how to create a NOT gate (inverter)
// by reusing the NAND gate module defined in nand.sv.
//
// When both inputs of a NAND gate are tied together, its behavior
// becomes identical to a NOT gate:
//
//   outY = ~(inA & inA)
//   outY = ~inA
//
//--------------------------------------------------------------
// TRUTH TABLE for NOT Gate
// -------------------------------------------------------------
// | inA | outY = ~inA |
// |------|--------------|
// |  0   |      1       |
// |  1   |      0       |
// -------------------------------------------------------------
//
//==============================================================

module not_using_nand (
    input  logic inA,   // Input signal to be inverted
    output logic outY   // Output: inverted version of inA
);

    // Instantiate the NAND gate module from nand.sv
    nand_gate u_nand (
        .inA(inA),   // Connect both inputs to inA
        .inB(inA),
        .outY(outY)  // Output of NAND becomes NOT output
    );

endmodule

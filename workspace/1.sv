// NAND gate module
module not_using_nand (
    input  logic a,
    output logic y
);
    // Instantiate the NAND module
    nand_gate u_nand (
        .a(a),
        .b(a),   // tie both inputs together
        .y(y)
    );
endmodule

// NAND Gate Reference Implementation
// This is a read-only reference file

module nand_gate (
    input a,
    input b,
    output y
);
    assign y = ~(a & b);
endmodule
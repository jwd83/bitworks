// NAND Gate Module - Level 1 Component
// BitWorks Digital Logic Design Course
// DO NOT MODIFY - This is a primitive component

module nand(
    input wire a,     // First input
    input wire b,     // Second input
    output wire y     // Output (NAND result)
);

    // NAND logic: output is LOW only when both inputs are HIGH
    assign y = ~(a & b);

endmodule

// NOT Gate Reference Implementation
// This is a read-only reference file

module not_gate (
    input a,
    output y
);
    assign y = ~a;
endmodule
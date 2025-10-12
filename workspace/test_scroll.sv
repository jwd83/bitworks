// Test file for scrolling functionality
// This file has many lines to test the editor scrolling

module test_scroll (
    input wire clk,
    input wire reset,
    input wire [7:0] data_in,
    output reg [7:0] data_out,
    output reg valid
);

// Line 10
reg [7:0] buffer [0:15];
reg [3:0] write_ptr;
reg [3:0] read_ptr;
reg [3:0] count;

// Line 15
always @(posedge clk or posedge reset) begin
    if (reset) begin
        write_ptr <= 0;
        read_ptr <= 0;
        count <= 0;
        // Line 20
        data_out <= 0;
        valid <= 0;
    end else begin
        // Write logic
        if (count < 16) begin
            // Line 25
            buffer[write_ptr] <= data_in;
            write_ptr <= write_ptr + 1;
            count <= count + 1;
        end
        
        // Line 30
        // Read logic
        if (count > 0) begin
            data_out <= buffer[read_ptr];
            valid <= 1;
            read_ptr <= read_ptr + 1;
            // Line 35
            count <= count - 1;
        end else begin
            valid <= 0;
        end
    end
    // Line 40
end

// More lines for testing
wire internal_signal_1;
wire internal_signal_2;
wire internal_signal_3;
// Line 45
wire internal_signal_4;
wire internal_signal_5;
wire internal_signal_6;
wire internal_signal_7;
wire internal_signal_8;
// Line 50

assign internal_signal_1 = clk & reset;
assign internal_signal_2 = |data_in;
assign internal_signal_3 = &data_out;
assign internal_signal_4 = ^data_in;
// Line 55
assign internal_signal_5 = ~valid;
assign internal_signal_6 = count[0];
assign internal_signal_7 = count[1];
assign internal_signal_8 = count[2];

// Line 60
// Additional test content
parameter MAX_COUNT = 16;
parameter MIN_COUNT = 0;
parameter DEFAULT_VALUE = 8'h00;

// Line 65
// Even more lines to ensure we have enough content for scrolling
localparam STATE_IDLE = 2'b00;
localparam STATE_READ = 2'b01;
localparam STATE_WRITE = 2'b10;
localparam STATE_FULL = 2'b11;
// Line 70

reg [1:0] current_state;
reg [1:0] next_state;

// State machine
always @(posedge clk or posedge reset) begin
    // Line 75
    if (reset) begin
        current_state <= STATE_IDLE;
    end else begin
        current_state <= next_state;
    end
    // Line 80
end

// Next state logic
always @(*) begin
    next_state = current_state;
    case (current_state)
        // Line 85
        STATE_IDLE: begin
            if (count == 0) begin
                next_state = STATE_WRITE;
            end
        end
        // Line 90
        STATE_WRITE: begin
            if (count == MAX_COUNT) begin
                next_state = STATE_FULL;
            end
        end
        // Line 95
        STATE_FULL: begin
            if (count < MAX_COUNT) begin
                next_state = STATE_READ;
            end
        end
        // Line 100
        STATE_READ: begin
            if (count == MIN_COUNT) begin
                next_state = STATE_IDLE;
            end
        end
        // Line 105
    endcase
end

endmodule

// End of test file - Line 110
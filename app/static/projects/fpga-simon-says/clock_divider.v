`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    13:28:31 11/27/2017 
// Design Name: 
// Module Name:    Cloc_divider 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////
module clock_divider(
    input in_clk,      // 100 MHz clock
    output reg out_clk // 1 Hz clock
);
	
	reg[32:0] count;

	initial begin
		count = 0;
        out_clk = 0; // initialize everything to zero
	end
	
	always @(negedge in_clk)
	begin
		// increment count by one (use blocking assignment)
		// if count equals to some big number (that you need to calculate),
		//     (Think: how many input clock cycles do you need to see 
		//     for it to be half a second)
		 if (count == 50_000_000) begin
            out_clk <= ~out_clk; //     then flip the output clock,   (use non-blocking assignment)
            count <= 0;          //     and reset count to zero.      (use non-blocking assignment)
         end else begin
            count = count + 1;
         end
	end


endmodule
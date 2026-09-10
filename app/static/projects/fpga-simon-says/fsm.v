`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/23/2023 08:43:13 AM
// Design Name: 
// Module Name: fsm
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module fsm(
        input clock,
        input [15:0] sixteen_bit_number,
        output [6:0] cathode,
        output reg [7:0] anode
    );
    
    reg [3:0] four_bit_number;
    // instantiate decoder that decodes the four bit number into the cathode
    reg [1:0] state; // stores state of FSM
    
    decoder dec (.number(four_bit_number), .cathode(cathode));
    
    initial begin
		state = 0;
		anode = 8'b11111111;
	end
    
    always @(posedge clock)
	begin
	   state <= state + 1;
	
        case(state)
        
           2'b00: begin
               anode = 8'b11111110;
               four_bit_number <= sixteen_bit_number [3:0];
           end
           2'b01: begin
               anode = 8'b11111101;
               four_bit_number <= sixteen_bit_number [7:4];
           end
           2'b10: begin
               anode = 8'b11111011;
               four_bit_number <= sixteen_bit_number [11:8];
           end
           2'b11: begin
               anode = 8'b11110111;
               four_bit_number <= sixteen_bit_number [15:12];
           end
            // increment state
            // set anode (which display do you want to set?)
            //   hint: if state == 0, then set only the LSB of anode to zero,
            //         if state == 1, then set only the second to LSB to zero.
            // set the four bit number to be the approprate slice of the 16-bit number
        endcase
    end
endmodule


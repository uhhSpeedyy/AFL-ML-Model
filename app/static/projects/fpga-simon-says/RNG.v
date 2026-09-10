`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/22/2026 12:11:33 PM
// Design Name: 
// Module Name: RNG
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

//REQUIRES RST TO INITIALIZE
//SET SEED TO A 16 BIT RANDOM NUMBER, SET LOAD TO 1 FOR 1 CLOCK CYCLE, AND SET IT BACK TO 0
//AT EACH CLOCK, OUT WILL GENERATE A RANDOM 16 BIT NUMBER

module RNG(clk,rst,load,seed,out);
input clk,rst;
input load;
input [15:0] seed;
output reg [15:0] out;

wire feedback = out[15] ^ out[14] ^ out[13] ^ out[12];
wire [15:0] nextOut;

assign nextOut = {out[14:0],feedback};

always @ (posedge clk or posedge rst)
begin
    if(rst)
    begin
        out <= 16'hFFFF;
    end
    else
    begin
        if(load)
            out <= seed;
        else
            out <= nextOut;
    end
end

endmodule



`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/22/2026 12:12:36 PM
// Design Name: 
// Module Name: RNG_Test
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

module RNG_Test(

    );
    
    reg clk, rst, load;
    reg [15:0] seed;
    wire [15:0] out;
    
    RNG DUT(clk,rst,load,seed,out);
    
    // Clock generator
    always #1 clk = ~clk;
    
    initial begin
        clk = 0;
        rst = 0;
        load = 1;
        seed = 56394;
        #1 rst = 0;
        #1 rst = 1;
        #1 rst = 0;
        #5 load = 0;
    end
    
    initial #100 $finish;
    
    
endmodule

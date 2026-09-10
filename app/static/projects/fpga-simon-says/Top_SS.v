`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/24/2026 09:47:09 AM
// Design Name: 
// Module Name: Top_SS
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


module Top_SS(
    input clock,
    input reset,
    input [3:0] button,
    output [3:0] LED,
    output [7:0] anode,
    output [6:0] cathode
    );
    
    wire SlowClock;
    wire FastClock;
    wire [3:0] CleanButton;
    wire [15:0] RNGvalue;
    wire [15:0] CurrentScore;
    
    clock_divider SlowClockInst (.in_clk(clock), .out_clk(SlowClock));
    
    faster_clock_divider FastClockInst (.in_clk(clock), .out_clk(FastClock));
    
    RNG RNGinst (.clk(FastClock), .rst(reset), .load(1'b0), .seed(16'b1100111010100101), .out(RNGvalue));
    
    debouncer DebouncerInst0 (.clock(clock), .NoisyButton(button[0]), .CleanButton(CleanButton[0]));
    debouncer DebouncerInst1 (.clock(clock), .NoisyButton(button[1]), .CleanButton(CleanButton[1]));
    debouncer DebouncerInst2 (.clock(clock), .NoisyButton(button[2]), .CleanButton(CleanButton[2]));
    debouncer DebouncerInst3 (.clock(clock), .NoisyButton(button[3]), .CleanButton(CleanButton[3]));
    
    SS_SM StateMachineInst (.button(CleanButton), .reset(reset), .clock(SlowClock), .FasterClock(FastClock), .RandomVal(RNGvalue[1:0]), .LED(LED), .score(CurrentScore));
    
    fsm FSMdisplayInst (.clock(FastClock), .sixteen_bit_number(CurrentScore), .cathode(cathode), .anode(anode));
    
endmodule

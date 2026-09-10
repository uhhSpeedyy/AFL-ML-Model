`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/13/2026 04:41:17 PM
// Design Name: 
// Module Name: debouncer
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


module debouncer #(MAX = 1000000) (
    input clock,
    input NoisyButton,
    output reg CleanButton
    );
    
    reg [19:0] count = 0;
    reg ButtonState = 0;
    
    always @(posedge clock) begin
        if (NoisyButton !== ButtonState) begin
            if (count < MAX) begin
                count <= count + 1;
            end else begin
                ButtonState <= NoisyButton;
                CleanButton <= NoisyButton;
                count <= 0;
            end
        end else begin
            count <= 0;
        end
    end            
endmodule


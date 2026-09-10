`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 10/23/2023 08:38:09 AM
// Design Name: 
// Module Name: decoder
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


module decoder(
        input [3:0] number,
        output reg [6:0] cathode
    );
    
    initial begin
        cathode = 7'b0000001;
    end
    
    always @(number)
    begin
        case(number)
            4'b0000:cathode<=7'b1000000;
            4'b0001:cathode<=7'b1111001;
            4'b0010:cathode<=7'b0100100;
            4'b0011:cathode<=7'b0110000;
            4'b0100:cathode<=7'b0011001;
            4'b0101:cathode<=7'b0010010;
            4'b0110:cathode<=7'b0000010;
            4'b0111:cathode<=7'b1111000;
            4'b1000:cathode<=7'b0000000;
            4'b1001: cathode<=7'b0010000;
            default: cathode<=7'b1111111;
        endcase
    end
    
endmodule

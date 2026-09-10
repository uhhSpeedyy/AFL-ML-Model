`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 04/22/2026 12:20:28 PM
// Design Name: 
// Module Name: SS_SM
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
module SS_SM(
    input [3:0] button,
    input reset,
    input clock,
    input FasterClock,
    input [1:0] RandomVal,
    output reg [3:0] LED,
    output reg [15:0] score
    );
    
    parameter Start = 3'b000;
    parameter Generate = 3'b001;
    parameter Sequence = 3'b010;
    parameter WaitForInput = 3'b011;
    parameter CheckInput = 3'b100;
    parameter RoundSuccess = 3'b101;
    parameter GameOver = 3'b110;
    
    reg [2:0] state; 
    
    reg [1:0] SequenceMemory [0:15];
    reg [3:0] CurrentLevel;
    reg [3:0] StepCounter;
    reg [3:0] PlayerStep;
    
    reg [3:0] TimeoutCounter;
    reg [1:0] FlashTimer;
    reg PreviousClockEdge;
    wire SecondsPassed;
    
    always @(posedge FasterClock) begin
        PreviousClockEdge <= clock;
    end
    
    assign SecondsPassed = (clock && !PreviousClockEdge);
    
    always @(posedge FasterClock or posedge reset) begin
        if (reset) begin
            state <= Start;
            LED <= 4'b0000;
            score <= 0;
            CurrentLevel <= 0;
        end else begin   
            case(state)
                Start: begin
                    score <= 0;
                    CurrentLevel <= 0;
                    LED <= 4'b0000;
                    if (button[3] | button[2] | button[1] | button[0]) begin
                        state <= Generate;
                    end
                end
                
                Generate: begin
                    SequenceMemory[CurrentLevel] <= RandomVal;
                    StepCounter <= 0;
                    FlashTimer <= 0;
                    state <= Sequence; 
                end
            
                Sequence: begin
                    if (SecondsPassed) begin
                        FlashTimer <= FlashTimer + 1;
                    end
                    
                    if (FlashTimer == 0) begin
                        LED <= 4'b0000;
                    end else if (FlashTimer == 1) begin
                        LED <= (4'b0001 << SequenceMemory[StepCounter]);
                    end else if (FlashTimer == 2) begin
                        LED <= 4'b0000;
                        FlashTimer <= 0;
                        StepCounter <= StepCounter + 1;
                    end
                    
                    if (StepCounter == CurrentLevel && FlashTimer == 2) begin
                        PlayerStep <= 0;
                        TimeoutCounter <= 0;
                        state <= WaitForInput;
                    end           
                end
                
                WaitForInput: begin
                    if (SecondsPassed) begin
                        TimeoutCounter <= TimeoutCounter + 1;
                    end
                    
                    if (TimeoutCounter >= 15) begin
                        state <= GameOver;
                    end else if (button[3] | button[2] | button[1] | button[0]) begin
                        state <= CheckInput;  
                    end           
                end
                
                CheckInput: begin
                    if (button == (4'b0001 << SequenceMemory[PlayerStep])) begin
                        state <= CheckInput;
                    end else if (button == 4'b0000) begin
                        if (PlayerStep == CurrentLevel) begin
                            state <= RoundSuccess;
                        end else begin
                            PlayerStep <= PlayerStep + 1;
                            state <= WaitForInput;
                        end 
                    end else begin    
                        state <= GameOver;
                    end
                end          
                
                RoundSuccess: begin
                    if (CurrentLevel < 15) begin
                        CurrentLevel <= CurrentLevel + 1;
                        score <= score + 1;
                        state <= Generate;
                    end else begin 
                        state <= GameOver;
                    end
                end    
                
                GameOver: begin
                    if (reset) begin
                        state <= Start;
                    end else if (SecondsPassed) begin
                        LED <= ~LED;
                    end
                end     
                
                default: state <= Start;         
            endcase
        end
    end           
    
endmodule

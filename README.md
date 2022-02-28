# Taiko no Tatsujin - Fumen Timing Window Replace Script

Simple Python 3 script to replace that can replace the timing windows in a Taiko Gen 3 fumen


Usage: replace_timing.py inFile outFile

Detects what difficulty timing window to use based on the Input's File name.  
Easy(\_e) and Normal(\_n) will use timing_easy.bin   
Hard(\_h), Extreme(\_e) and Ura(\_x) will use timing_hard.bin  

Any input file without a difficulty in it's file name  
Will default to using timing_hard.bin instead  

Edit "timing_easy.bin" and "timing_hard.bin" to change the values
By default, they use the default Timing Windows

The Timing values are in the single floating-point format and it goes in this order:  
GOOD(良), OK(可) and then BAD(不可) - Repeated 9 times (likely for each note-type)  
Each judgement is 16 bytes long  

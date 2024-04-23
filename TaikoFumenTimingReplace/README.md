# Taiko no Tatsujin - Fumen Timing Window Replace Script

Simple Python 3 script to replace that can replace the timing windows in a Taiko Gen 3 fumen  

Usage: replace_timing.py inFile outFile timingWindow  

Timing Options: Standard, Hitnarrow, Hitwide or a User Defined Option.  


Detects what difficulty timing window to use based on the Input's filename.  
Easy(\_e) and Normal(\_n) will use the easy timing  
Hard(\_h), Extreme(\_e) and Ura(\_x) will use hard timing  

If it fails to detect difficulty, it'll use the hard timing values instead.  

To add custom timing values, add a new section to timing.ini and define it's name and add values for each judgement.  
A template can be found [here](TaikoFumenTimingReplace/resource/template.ini)  

# Credits

swigz27 - Initial code.  
Yuki [(Nerdy-boi)](https://github.com/Nerdy-boi) - Code optimisations and tweaks.  

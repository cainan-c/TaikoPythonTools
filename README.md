# Taiko no Tatsujin Fumen Timing Window Replace Script

Simple Python 3 script to replace that can replace the timing windows in a Taiko Gen 3 fumen


Usage: replace_timing.py inFile outFile

Detects what difficulty timing window to use based on the Input's File name.
Easy(\_e) and Normal(\_n) will use timing_easy.bin
Hard(\_h), Extreme(\_e) and Ura(\_x) will use timing_hard.bin

Any input file without a diffuclty on it will use timing_hard.bin

Edit "timing_easy.bin" and "timing_hard.bin" to change the values
By default, they use the default Timing Windows

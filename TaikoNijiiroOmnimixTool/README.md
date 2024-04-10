# Taiko no Tatsujin - Omnimix Creation Tool

(Not so) Simple Python 3 scripts that find and add back missing/removed songs to newer versions of Taiko Nijiiro  

Setup: 
Extract/Dump/Decrypt the following `datatable` files from your newest build of the game:    
`music_ai_section`, `music_attribute`, `music_order`, `music_usbsetting`, `musicinfo` and `wordlist` to the folder called `datatable`  

Do the same but for the versions you want to extract songs from, and place them in their designated folders.  
Example: `musicinfo.json` from JPN00 will go in the `musicinfo` folder with the prefix `_JPN00`  
`musicinfo/musicinfo_JPN00.json` etc etc.   

Edit `config.toml` to specify the paths to the game's you're adding entries from along with an output folder.   

Your folders should look a little something like this:  
![file explorer window](https://i.imgur.com/FdcaYue.png)

Once everything is properly defined, run `_run.py`. If everything is properly set up, two folders should appear in your output folder:  
`sound` and `datatable`  
(as `fumen` files are always present for removed songs, we do not need to worry about them.) 

Assuming this is for newer releases, this tool also automatically handles encryption, so all that's needed is to just drag and drop your output folders onto the game.  

As always, make sure to backup your files before modification.  

Should support every version of Taiko Nijiiro that uses encryption, this also handles adding `music_ai_section` entries to added back older songs also.  

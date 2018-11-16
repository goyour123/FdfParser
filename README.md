# FdParser - EDK2 FDF file Parser
------

## FdfParser.py - python3 script for parsing FDF file
### Usage
Parse the FDF file
````
python FdfParser.py [FDF_filepath]
````
[FDF_filepath] is the OS file path of the FDF file.
The parsing result would save into the region.txt.

### config.json
The config.json is generated by FdfParser.py and contains the infomation of the FDF file last time used and switch cases in FDF file.
User could adjust the switch value in config.json for parsing in different conditions.

## FdfParser.py - python3 script for restoring the MACRO define in FDF file
### Usage
Restore the MACRO value into the FDF file which declared in the config.json
````
python FdfRestorer.py [MACRO] [Size]
````
[MACRO] is the MACRO define in FDF file path and [Size] would be the new MACRO value.
The FdfParser.py is needed to run before running the FdfRestorer.py to generate the config.json.

## FdVisualizer.py - GUI FDF file Parser
### Usage
````
python FdVisualizer.py
````
### Windows Execution File
[FdVisualizer.exe] (build/exe.win32-3.6/FdVisualizer.exe)

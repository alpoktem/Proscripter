# Proscripter

Creates acoustically enhanced speech transcripts from audio/transcript pair.

This library is an extension to the work by @laic (https://github.com/laic/prosody). 

## Requirements
- Praat (should be runnable from command line as "praat" or binary should be linked in `lib/laic/extract-prosodic-feats.sh`)
- R with packages: 
	- plyr
	- data.table
	- geometry
	- magic
	- abind
	- mFilter 

- `Python 2.7` with packages: 
	- numpy

## Sample Data
A sample recording is provided under directory `sampledata` together with its alignment file

## Run
To extract prosodic features of an aligned soundfile:
`lib/laic/extract-prosodic-feats.sh <wav-file> <alignment-file> <output-directory>`

This script collects fundamental frequency (f0)  and intensity features under aggs files 

To convert f0/intensity data to Proscript format:
`python src/proscripter.py -l <alignment-file> -f <f0-aggs-file> -i <i0-aggs-file> -o <output-proscript-file> -c <output-csv-file>`

A runnable bash script is in `run_example.sh`

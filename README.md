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
	- polynom

- `Python 2.7` with packages: 
	- numpy

## Sample Data
A sample recording is provided under directory `sampledata` together with its alignment file

## Run
To extract prosodic features of an aligned soundfile:
`lib/laic/extract-prosodic-feats.sh <wav-file> <alignment-file> <output-directory>`

This script collects fundamental frequency (f0)  and intensity measurements under the specified output directory

To convert f0/intensity data to Proscript format:
`python src/proscripter.py -d <prosodic-feats-directory> -l <alignment-file>`

where `<prosodic-feats-directory>` is the output directory of the previous call.

Both processes are combined in `run.sh`:
`./run.sh <wav-file> <alignment-file> <output-directory>`

For batch processing, prepare a text file with a list of audio/alignment pairs seperated by tab and run:
`./run_batch.sh <file-pair-list> <output-directory>`

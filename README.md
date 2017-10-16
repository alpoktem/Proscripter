Proscripter - Creates acoustically enhanced speech transcripts from audio/transcript pair.

REQUIREMENTS
Praat (should be runnable from command line as "praat" or binary should be linked in lib/laic/extract-prosodic-feats.sh)
R with packages plyr, data.table, (geometry, magic, abind, mFilter)
Python (ver 2.7) with packages optparse, pandas, csv, cPickle, numpy, collections

SAMPLE DATA
A sample recording is provided under directory [sampledata] together with its alignment file

RUN
To extract prosodic features of an aligned soundfile:
lib/laic/extract-prosodic-feats.sh <wav-file> <alignment-file> <output-directory>

This script collects f0 and intensity features under aggs files 

To convert f0/intensity data to Proscript format:
python lib/etc/proscripter.py -l <alignment-file> -f <f0_aggs_file> -i <$i0_aggs_file> -o <output-proscript-file> -c <output-csv-file>






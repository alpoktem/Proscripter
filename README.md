krisPunk - Punctuation generation module. Punctuates raw ASR transcription using prosodic features. 

REQUIREMENTS
Praat (should be runnable from command line as "praat" or binary should be linked in extract-prosodic-feats.sh)
R with libraries plyr, data.table

RUN
To extract prosodic features of an aligned soundfile:
lib/laic/extract-prosodic-feats.sh <wav-file> <alignment-file> <output-directory>

The alignment file has 4 columns (word.id, starttime, endtime, word) and rows for each word




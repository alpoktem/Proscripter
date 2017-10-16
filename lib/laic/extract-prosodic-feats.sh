#!/bin/bash

## Get raw F0 and intensity features using praat.  

PRAAT=praat 		#link to praat binary
wavfile=$1		    ## i.e. where the wav file is
alignfile=$2		## Segmentation file, see for example ~/lubbock/data/ted-trans/derived/alignseg/${ALTCONV}.alignseg.txt" 
outdir=$3 		    ## This is the output directory 	

wavbase=$(basename "$wavfile")
file_id="${wavbase%.*}"

echo Processing $file_id

mkdir -p $outdir/$file_id
mkdir -p $outdir/$file_id/raw-f0
mkdir -p $outdir/$file_id/raw-i0

tail -n +2 $alignfile |
while read line
do
	#CAREFUL HERE. CHANGED ALIGNFILE STRUCTURE
	wordid=`echo $line | cut -d " " -f 8`
	start=`echo $line | cut -d " " -f 6`
	end=`echo $line | cut -d " " -f 7`

	outfilename=$wordid

    #FOR AUDIO SEGMENTATION
    #wavsegmentdir=$outdir/$conv-wav
    #mkdir -p $wavsegmentdir
	#echo  $wavfile $outfile $start $end $indir $outdir $conv 
	#echo `which praat`
	#duration=`echo - | awk -v end=$end -v start=$start '{print end - start}'`
	#echo avconv -i $wavfile -ss $start -t $duration -ac 1 -ar 16000 $wavsegmentdir/$wordid.wav
	
	#EXTRACT RAW FEATURES USING PRAAT
	praat extract-feats.praat $wavfile $outfilename $start $end $outdir/$file_id
	
done  

#Merge segmented f0 and intensity contours into one file USING R
RScript get-pros-norm.r $file_id f0 $outdir/$file_id/raw-f0/ $outdir/$file_id/ $alignfile
RScript get-pros-norm.r $file_id i0 $outdir/$file_id/raw-i0/ $outdir/$file_id/ $alignfile

#extract normalized prosody features
RScript get-pros-window.r $file_id f0 $outdir/$file_id $alignfile
RScript get-pros-window.r $file_id i0 $outdir/$file_id $alignfile

#exit 0


#to extract raw f0/i0 features:
wavfile=/Users/alp/phdCloud/playground/krisPunk/sampledata/AlGore2006.0003.wav
alignfile=/Users/alp/phdCloud/playground/krisPunk/sampledata/AlGore2006.0003.align
output_dir=/Users/alp/phdCloud/playground/krisPunk/out


lib/laic/extract-prosodic-feats.sh $wavfile $alignfile $output_dir


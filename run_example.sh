curr_dir=`pwd`

#to extract raw f0/i0 features:
file_id=AlGore2006.0003
wavfile=$curr_dir/sampledata/AlGore2006.0003.wav
alignfile=$curr_dir/sampledata/AlGore2006.0003.align
#alignfile=/Users/alp/phdCloud/playground/krisPunk/sampledata/ay.align
output_dir=$curr_dir/out

cd lib/laic
echo ./extract-prosodic-feats.sh $wavfile $alignfile $output_dir

cd $curr_dir

#Convert aggs features into Proscript format
f0_aggs_file="$output_dir/$file_id/f0/`ls $output_dir/$file_id/f0 | grep aggs`"
i0_aggs_file="$output_dir/$file_id/i0/`ls $output_dir/$file_id/i0 | grep aggs`"
python src/proscripter.py -l $alignfile -f $f0_aggs_file -i $i0_aggs_file -o $output_dir/$file_id/$file_id.pcl -c $output_dir/$file_id/$file_id.csv



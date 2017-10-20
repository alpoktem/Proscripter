get_abs_filename() {
  # $1 : relative filename
  echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

curr_dir=`pwd`
wavfile=`get_abs_filename $1`
alignfile=`get_abs_filename $2`
output_dir=`get_abs_filename $3`

wavfilename=$(basename "$wavfile")
file_id="${wavfilename%.*}"

if [ -z "$output_dir" ]
then
      echo "Creating output directory"
fi


cd lib/laic
./extract-prosodic-feats.sh $wavfile $alignfile $output_dir
cd $curr_dir

#Convert aggs features into Proscript format
f0_aggs_file="$output_dir/$file_id/f0/`ls $output_dir/$file_id/f0 | grep aggs`"
i0_aggs_file="$output_dir/$file_id/i0/`ls $output_dir/$file_id/i0 | grep aggs`"
python src/proscripter.py -l $alignfile -f $f0_aggs_file -i $i0_aggs_file -o $output_dir/$file_id/$file_id.pcl -c $output_dir/$file_id/$file_id.csv



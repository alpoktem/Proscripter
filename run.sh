curr_dir=`pwd`

#to extract raw f0/i0 features:



wavfile=$1
alignfile=$2
output_dir=$3

get_abs_filename() {
  # $1 : relative filename
  echo "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
}

wavfilename=$(basename "$wavfile")
file_id="${wavfilename%.*}"

wavfile=`get_abs_filename $wavfile`
alignfile=`get_abs_filename $2`


cd lib/laic
./extract-prosodic-feats.sh $wavfile $alignfile $output_dir

cd $curr_dir

#Convert aggs features into Proscript format
f0_aggs_file="$output_dir/$file_id/f0/`ls $output_dir/$file_id/f0 | grep aggs`"
i0_aggs_file="$output_dir/$file_id/i0/`ls $output_dir/$file_id/i0 | grep aggs`"
python src/proscripter.py -l $alignfile -f $f0_aggs_file -i $i0_aggs_file -o $output_dir/$file_id/$file_id.pcl -c $output_dir/$file_id/$file_id.csv



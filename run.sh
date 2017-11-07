#Processes a wav and alignment file pair
PROSCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

cd $PROSCRIPT_DIR/lib/laic
./extract-prosodic-feats.sh $wavfile $alignfile $output_dir
cd $curr_dir

python $PROSCRIPT_DIR/src/proscripter_v2.py -d $output_dir/$file_id -l $alignfile -i $file_id #-f pause_before -f f0_mean

# Creates a sequence of features given feature files of ted corpus
from __future__ import print_function
from optparse import OptionParser
import os
import sys
import re
import csv
import cPickle
from random import randint
from collections import OrderedDict
import numpy as np

csv.field_size_limit(1000000000000) 

features_f0_header = 'mean.normF0\tsd.normF0\tmax.normF0\tmin.normF0\tmedian.normF0\tq1.normF0\tq2.5.normF0\tq5.normF0\tq25.normF0\tq75.normF0\tq95.normF0\tq97.5.normF0\tq99.normF0\tslope.normF0\tintercept.normF0\tmean.normF0.slope\tsd.normF0.slope\tmax.normF0.slope\tmin.normF0.slope\tmedian.normF0.slope\tq1.normF0.slope\tq2.5.normF0.slope\tq5.normF0.slope\tq25.normF0.slope\tq75.normF0.slope\tq95.normF0.slope\tq97.5.normF0.slope\tq99.normF0.slope\tslope.normF0.slope\tintercept.normF0.slope'
features_i0_header = 'mean.normI0\tsd.normI0\tmax.normI0\tmin.normI0\tmedian.normI0\tq1.normI0\tq2.5.normI0\tq5.normI0\tq25.normI0\tq75.normI0\tq95.normI0\tq97.5.normI0\tq99.normI0\tslope.normI0\tintercept.normI0\tmean.normI0.slope\tsd.normI0.slope\tmax.normI0.slope\tmin.normI0.slope\tmedian.normI0.slope\tq1.normI0.slope\tq2.5.normI0.slope\tq5.normI0.slope\tq25.normI0.slope\tq75.normI0.slope\tq95.normI0.slope\tq97.5.normI0.slope\tq99.normI0.slope\tslope.normI0.slope\tintercept.normI0.slope'

SPACE = "_"
PUNCTUATION_VOCABULARY = {0:SPACE, 1:',', 2:'.', 3:'?', 4:'!', 5:'-', 6:';', 7:':'}
INV_PUNCTUATION_CODES = {SPACE:0, ',':1, '.':2, '?':3, '!':4, '-':5, ';':6, ':':7, '':0}
REDUCED_PUNCTUATION_VOCABULARY = {0:SPACE, 1:',', 2:'.', 3:'?'}
REDUCED_INV_PUNCTUATION_CODES = {SPACE:0, ',':1, '.':2, '?':3, '':0}
EOS_PUNCTUATION_CODES = [2,3,4,5,6,7]

FLOAT_FORMATTING="{0:.4f}"
END_TOKEN = "<END>" 

class Word:
	def __init__(self):
		self.word = None

		self.pause_before = -1.0  			#seconds
		self.pause_after = -1.0				#seconds
		self.duration = -1.0				#seconds
		self.speech_rate_phon = -1			#seconds
		self.speech_rate_normalized = -1
		self.f0_contour = -1
		self.i0_contour = -1
		self.contour_xaxis = -1 
		self.f0_mean = -1.0
		self.i0_mean = -1.0
		self.f0_slope = -1.0
		self.i0_slope = -1.0
		self.f0_median = -1.0
		self.i0_median = -1.0
		self.f0_sd = -1.0
		self.i0_sd = -1.0
		self.f0_range = -1.0
		self.i0_range = -1.0
		
		self.pos = None
		self.punctuation_before = None
		self.punctuation_after = None

		self.end_time = -1.0
		self.start_time = -1.0

class Proscript:
    def __init__(self):
    	self.wordlist = []

    def addWord(self, word):
    	self.wordlist.append(word)

    def getLastWord(self):
    	if self.getLength() > 0:
    		return self.wordlist[-1]
    	else:
    		return None

    def getLength(self):
    	return len(self.wordlist)

def puncProper(punc):
	if punc in INV_PUNCTUATION_CODES.keys():
		return punc
	else:
		return puncEstimate(punc)

def reducePuncCode(puncCode):
	if puncCode in [4, 5, 6, 7]: #period
		return 2
	else:
		return puncCode

def reducePunc(punc):
	puncCode = INV_PUNCTUATION_CODES[punc]
	reducedPuncCode = reducePuncCode(puncCode)
	return PUNCTUATION_VOCABULARY[reducedPuncCode]

def puncEstimate(punc):
	if '.' in punc:
		return '.'
	elif ',' in punc:
		return ','
	elif '?' in punc:
		return '?'
	elif '!' in punc:
		return '!'
	elif ':' in punc:
		return ':'
	elif ';' in punc:
		return ';'
	elif '-' in punc:
		return '-'
	else:
		return ''

def checkFile(filename, variable):
    if not filename:
        sys.exit("%s file not given"%variable)
    else:
        if not os.path.isfile(filename):
            sys.exit("%s file %s does not exist"%(variable, filename))

def checkFolder(dir, variable):
	if not os.path.exists(dir):
		sys.exit("%s directory not given"%variable)

def readTedDataToMemory(file_wordalign, file_wordaggs_f0, file_wordaggs_i0, dir_raw_f0=None, dir_raw_i0=None):

	#read wordaggs_f0 file to a dictionary 
	word_id_to_f0_features_dic = {}
	at_header_line = 1
	with open(file_wordaggs_f0, 'rt') as f:
		reader = csv.reader(f, delimiter=' ', quotechar=None)
		for row in reader:
			if at_header_line:
				at_header_line = 0
			else:
				word_id_to_f0_features_dic[row[0]] = featureVectorToFloat(row[6:36])

	#read wordaggs_i0 file to a dictionary
	word_id_to_i0_features_dic = {}
	at_header_line = 1
	with open(file_wordaggs_i0, 'rt') as f:
		reader = csv.reader(f, delimiter=' ', quotechar=None)
		for row in reader:
			if at_header_line:
				at_header_line = 0
			else:
				word_id_to_i0_features_dic[row[0]] = featureVectorToFloat(row[6:36])  #acoustic features

	#read aligned word file to a dictionary (word.align)
	word_data_aligned_dic = OrderedDict()
	with open(options.file_wordalign, 'rt') as f:
		reader = csv.reader(f, delimiter='\t', quotechar=None)
		first_line = 1
		for row in reader:
			if first_line:
				first_line = 0
				continue
			word_data_aligned_dic[row[7]] = [row[5], row[6], row[9]] #starttime, endtime, word

	#if raw folders are given read files under for f0/i0 contours
	word_id_to_raw_f0_features_dic = {}
	for word_id in word_id_to_f0_features_dic.keys():
		file_f0_vals = os.path.join(dir_raw_f0, "%s.PitchTier"%word_id)
		word_id_to_raw_f0_features_dic[word_id] = []
		if os.path.exists(file_f0_vals):
			with open(file_f0_vals, 'rt') as f:
				reader = csv.reader(f, delimiter='\t', quotechar=None)
				duration = 1
				for row in reader:
					if len(row) == 1:
						if len(row[0].split()) == 3:	#this row has the duration information
							duration = float(row[0].split()[1])
					elif len(row) == 2:	#only rows with two values carry pitch information. rest is metadata
						time_percentage = int((float(row[0]) / duration) * 100)
						f0_val = [time_percentage, round(float(row[1]), 3)]
						word_id_to_raw_f0_features_dic[word_id].append(f0_val)

	#if raw folders are given read files under for f0/i0 contours
	word_id_to_raw_i0_features_dic = {}
	for word_id in word_id_to_i0_features_dic.keys():
		file_i0_vals = os.path.join(dir_raw_i0, "%s.IntensityTier"%word_id)
		word_id_to_raw_i0_features_dic[word_id] = []
		if os.path.exists(file_i0_vals):
			with open(file_i0_vals, 'rt') as f:
				reader = csv.reader(f, delimiter='\t', quotechar=None)
				line_type = 0	#0 - meta, 1 - time info, 2 - intensity value
				row_count = 0
				for row in reader:
					row_count += 1
					if line_type == 1:
						time_percentage = int((float(row[0]) / duration) * 100)
						line_type = 2
					elif line_type == 2:
						word_id_to_raw_i0_features_dic[word_id].append( [time_percentage, round(float(row[0]), 3)] )
						line_type = 1
					else:
						if row_count == 5:
							duration = round(float(row[0]), 2)
						elif row_count == 6:
							line_type = 1					

	return [word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic]

def featureVectorToFloat(featureVector):
	features_fixed = [0.0] * len(featureVector)
	for ind, val in enumerate(featureVector):
		if val == 'NA':
			features_fixed[ind] = 0.0
		else:
			features_fixed[ind] = float(FLOAT_FORMATTING.format(float(val)))
	return features_fixed

def structureData(word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic=None, word_id_to_raw_i0_features_dic=None):
	proscript = Proscript()
	sum_speech_rate_phon = 0.0
	sum_speech_rate_syll = 0.0
	count_speech_rate_syll = 0
	count_speech_rate_phon = 0

	for word_id, word_data in word_data_aligned_dic.items():
		word = Word()

		print(word_id)
		print(word_data)

		if not word_data[0] == "NA": 
			word.start_time = float(word_data[0])
		if not word_data[1] == "NA": 
			word.end_time = float(word_data[1])

		word_stripped = word_data[2]
		word_stripped = word_stripped[re.search(r"\w", word_stripped).start():]
		word_stripped = word_stripped[::-1]
		word_stripped = word_stripped[re.search(r"\w", word_stripped).start():]
		word_stripped = word_stripped[::-1]

		word.word = word_stripped

		#pause values
		if not word.start_time == -1 and not proscript.getLastWord() == None and not proscript.getLastWord().end_time == -1:
			diff = word.start_time - proscript.getLastWord().end_time
		else: 
			diff = 0.0
		word.pause_before = float(FLOAT_FORMATTING.format(diff))

		#word duration
		if not word.start_time == -1 and not word.end_time == -1:
			diff = word.end_time - word.start_time
		else:
			diff = 0.0
		word.duration = float(FLOAT_FORMATTING.format(diff))

		#speech rate with respect to phonemes (no of characters)
		no_of_characters = len(re.sub('[^a-zA-Z]','', word.word))
		speech_rate_phon = word.duration / no_of_characters
		word.speech_rate_phon = float(FLOAT_FORMATTING.format(speech_rate_phon))

		if word.speech_rate_phon > 0:
			sum_speech_rate_phon += word.speech_rate_phon
			count_speech_rate_phon += 1

		#acoustic features
		word.f0_mean = float(word_id_to_f0_features_dic[word_id][0])
		word.i0_mean = float(word_id_to_i0_features_dic[word_id][0])
		word.f0_slope = float(word_id_to_f0_features_dic[word_id][14])
		word.i0_slope = float(word_id_to_i0_features_dic[word_id][14])
		word.f0_sd = float(word_id_to_f0_features_dic[word_id][1])
		word.i0_sd = float(word_id_to_i0_features_dic[word_id][1])
		word.f0_range = float(word_id_to_f0_features_dic[word_id][2]) - float(word_id_to_f0_features_dic[word_id][3])
		word.i0_range = float(word_id_to_i0_features_dic[word_id][2]) - float(word_id_to_i0_features_dic[word_id][3])

		#contours
		word.f0_contour = word_id_to_raw_f0_features_dic[word_id]
		word.i0_contour = word_id_to_raw_i0_features_dic[word_id]
		
		#punctuation
		#...
		proscript.addWord(word)
	
	return proscript

def word_data_to_pickle(talk_data, output_pickle_file):
	with open(output_pickle_file, 'wb') as f:
		cPickle.dump(talk_data, f, cPickle.HIGHEST_PROTOCOL)

def word_data_to_csv(talk_data, output_csv_file):
	with open(output_csv_file, 'wb') as f:
		w = csv.writer(f, delimiter="\t")
		rowIds = ['word', 'punctuation', 'word.duration', 'speech.rate.norm', 'pause', 'mean.f0', 'range.f0', 'mean.i0', 'range.i0']
		w.writerow(rowIds)
		rows = zip( talk_data[rowIds[0]],
					talk_data[rowIds[1]],
					talk_data[rowIds[2]],
					talk_data[rowIds[3]],
					talk_data[rowIds[4]],
					talk_data[rowIds[5]],
					talk_data[rowIds[6]],
					talk_data[rowIds[7]],
					talk_data[rowIds[8]])
		for row in rows:                                        
			w.writerow(row) 

def convert_value_to_level(pause_dur, pause_bins):
	level = 0
	for bin_no, bin_upper_limit in enumerate(pause_bins):
		if pause_dur > bin_upper_limit:
			level += 1
		else:
			break
	return level

def create_pause_bins():
	bins = np.arange(0, 1, 0.05)
	bins = np.concatenate((bins, np.arange(1, 2, 0.1)))
	bins = np.concatenate((bins, np.arange(2, 5, 0.2)))
	bins = np.concatenate((bins, np.arange(5, 10, 0.5)))
	bins = np.concatenate((bins, np.arange(10, 20, 1)))
	return bins

def create_semitone_bins():
	bins = np.arange(-20, -10, 1)
	bins = np.concatenate((bins, np.arange(-10, -5, 0.5)))
	bins = np.concatenate((bins, np.arange(-5, 0, 0.25)))
	bins = np.concatenate((bins, np.arange(0, 5, 0.25)))
	bins = np.concatenate((bins, np.arange(5, 10, 0.5)))
	bins = np.concatenate((bins, np.arange(10, 20, 1)))
	return bins

def wordDataToDictionary(structured_word_data, avg_speech_rate):
	actualword_seq = []
	#speech_rate_syll_seq = []
	speech_rate_phon_seq = []
	speech_rate_normalized_seq = []
	word_dur_seq = []
	punc_seq = []
	punc_reduced_seq = []
	pause_before_seq = []
	meanf0_seq = []
	medf0_seq = []
	meani0_seq = []
	slopef0_seq = []
	sdf0_seq = []
	jumpf0_seq = []
	jumpi0_seq = []
	rangef0_seq = []
	rangei0_seq = []
	#id sequences
	meanf0_id_seq = []
	meani0_id_seq = []
	rangef0_id_seq = []
	rangei0_id_seq = []
	pause_id_seq = []
	punctuation_id_seq = []
	reduced_punctuation_id_seq = []

	pause_bins = create_pause_bins()
	semitone_bins = create_semitone_bins()

	for word_datum in structured_word_data:
		actualword_seq += [word_datum['word']]
		word_dur_seq += [word_datum['word_dur']]
		punc_seq += [word_datum['minimal_punc_before']]
		punc_reduced_seq += [reducePunc(word_datum['minimal_punc_before'])]
		pause_before_seq += [word_datum['pause_before_dur']]
		meanf0_seq += [word_datum['features_f0'][0]]
		meani0_seq += [word_datum['features_i0'][0]]
		sdf0_seq += [word_datum['features_f0'][1]]
		medf0_seq += [word_datum['features_f0'][4]]
		slopef0_seq += [word_datum['features_f0'][14]]
		jumpf0_seq += [word_datum['mean.f0_jump_from_prev']]
		jumpi0_seq += [word_datum['mean.i0_jump_from_prev']]
		rangef0_seq += [word_datum['range.f0']]
		rangei0_seq += [word_datum['range.i0']]
		#id sequences
		meanf0_id_seq += [convert_value_to_level(word_datum['features_f0'][0], semitone_bins)]
		meani0_id_seq += [convert_value_to_level(word_datum['features_i0'][0], semitone_bins)]
		rangef0_id_seq += [convert_value_to_level(word_datum['range.f0'], semitone_bins)]
		rangei0_id_seq += [convert_value_to_level(word_datum['range.i0'], semitone_bins)]
		pause_id_seq += [convert_value_to_level(word_datum['pause_before_dur'], pause_bins)]
		#punctuation
		punctuation_id = INV_PUNCTUATION_CODES[word_datum['minimal_punc_before']]
		punctuation_id_seq += [punctuation_id]
		reduced_punctuation_id_seq += [reducePuncCode(punctuation_id)]
		#speech rate
		#speech_rate_syll_seq += [word_datum['speech.rate.syll']]
		speech_rate_phon_seq += [word_datum['speech.rate.phon']]
		normalized_speech_rate = (word_datum['speech.rate.phon'] / avg_speech_rate)
		if not normalized_speech_rate == 0.0:
			speech_rate_normalized_seq += [float(FLOAT_FORMATTING.format(normalized_speech_rate))]
		else:
			speech_rate_normalized_seq += [1.0]


	metadata = {'no_of_semitone_levels': len(semitone_bins),
				'no_of_pause_levels': len(pause_bins),
				'no_of_words': len(actualword_seq),
				'avg_speech_rate': avg_speech_rate
	}

	talk_data = {  'word': actualword_seq,
				   'word.duration': word_dur_seq ,
				   #'speech.rate.syll' : speech_rate_syll_seq,
				   'speech.rate.phon': speech_rate_phon_seq,
				   'speech.rate.norm': speech_rate_normalized_seq ,
				   'punctuation': punc_seq,
				   'punctuation.reduced': punc_reduced_seq,
				   'pause': pause_before_seq,
				   'pause.id': pause_id_seq,
				   'mean.f0': meanf0_seq,
				   'mean.i0': meani0_seq,
				   'med.f0': medf0_seq,
				   'slope.f0': slopef0_seq,
				   'sd.f0': sdf0_seq,
				   'jump.f0': jumpf0_seq,
				   'jump.i0': jumpi0_seq ,
				   'range.f0': rangef0_seq,
				   'range.i0': rangei0_seq ,
				   'mean.f0.id': meanf0_id_seq,
				   'mean.i0.id': meani0_id_seq,
				   'range.f0.id': rangef0_id_seq,
				   'range.i0.id': rangei0_id_seq,
				   'punc.id': punctuation_id_seq,
				   'punc.red.id': reduced_punctuation_id_seq,
				   'metadata': metadata
	}
	return talk_data

def findAggsFile(working_directory, feat):
	feat_dir = os.path.join(working_directory, feat)
	if os.path.exists(feat_dir):
		for file in os.listdir(feat_dir):
			if file.endswith("aggs.txt"):
				return os.path.join(working_directory, feat, file)
	sys.exit("Cannot find %s aggs file"%feat)

def main(options):
	checkFolder(options.dir_working, "dir_working")
	checkFile(options.file_wordalign, "file_wordalign")

	file_wordaggs_f0 = findAggsFile(options.dir_working, "f0")
	file_wordaggs_i0 = findAggsFile(options.dir_working, "i0")

	dir_raw_f0 = os.path.join(options.dir_working, "raw-f0")
	dir_raw_i0 = os.path.join(options.dir_working, "raw-i0")

	[word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic] = readTedDataToMemory(options.file_wordalign, file_wordaggs_f0, file_wordaggs_i0, dir_raw_f0, dir_raw_i0)
	proscript = structureData(word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic)

	#talk_data = wordDataToDictionary(structured_word_data, avg_speech_rate)

	#dir_proscript = os.path.join(options.dir_working, "proscript")
	#if not os.path.exists(dir_proscript):
	#	os.makedirs(dir_proscript)
	#word_data_to_pickle(talk_data, os.path.join(dir_proscript, "%s.pcl"%options.id_file))
	#word_data_to_csv(talk_data, os.path.join(dir_proscript, "%s.csv"%options.id_file))
	return 1

if __name__ == "__main__":
	usage = "usage: %prog [-s infile] [option]"
	parser = OptionParser(usage=usage)
	#parser.add_option("-a", "--audio", dest="file_audio", default=None, help="wav", type="string")
	parser.add_option("-l", "--align", dest="file_wordalign", default=None, help="word.txt.norm.align", type="string")	#in /txt-sent
	parser.add_option("-d", "--dir_working", dest="dir_working", default=None, help="Working directory where prosodic parameters and output is stored", type="string")
	parser.add_option("-i", "--id", dest="id_file", default="proscript", help="file id", type="string")	#in /txt-sent

	(options, args) = parser.parse_args()

	print("=====Proscripter=====")
	
	if main(options):
		print("Proscripted.")
	else:
		print("Failed.")
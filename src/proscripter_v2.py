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
		self.f0_contour_xaxis = -1 
		self.i0_contour_xaxis = -1 
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

	def get_value(self, property_name):
		value = getattr(self, property_name)
		return value

class Proscript:
	def __init__(self):
		self.word_list = []
		self.feature_set = ["word", "start_time", "end_time", "duration", "pause_before", "speech_rate_phon", "f0_mean", "i0_mean", "f0_slope", "i0_slope", "f0_sd", "i0_sd", "f0_range", "i0_range", "f0_contour_xaxis", "f0_contour", "i0_contour_xaxis", "i0_contour"]

	def add_word(self, word):
		self.word_list.append(word)

	def get_last_word(self):
		if self.get_length() > 0:
			return self.word_list[-1]
		else:
			return None

	def get_length(self):
		return len(self.word_list)

	def get_sequence(self, property_name):
		sequence = []
		for word in self.word_list:
			sequence.append(word.get_value(property_name))
		return sequence

	def get_leveled_sequence(self, property_name, bins):
		sequence = []
		for word in self.word_list:
			sequence.append(word.get_value_in_level(property_name, bins))
		return sequence

	def to_csv(self, csv_filename, feature_set=None):
		if not feature_set:
			feature_set = self.feature_set
		with open(csv_filename, 'wb') as f:
			w = csv.writer(f, delimiter="\t")
			rowIds = feature_set
			w.writerow(rowIds)

			for word in self.word_list:
				row = [word.get_value(feature_id) for feature_id in feature_set]                                     
				w.writerow(row) 

#--vvv--Punctuation helper functions--vvv--
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
#--^^^--Punctuation helper functions--^^^--

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

def structureData(word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic=None, word_id_to_raw_i0_features_dic=None):
	proscript = Proscript()
	
	sum_speech_rate_phon = 0.0
	sum_speech_rate_syll = 0.0
	count_speech_rate_syll = 0
	count_speech_rate_phon = 0

	for word_id, word_data in word_data_aligned_dic.items():
		word = Word()

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
		if not word.start_time == -1 and not proscript.get_last_word() == None and not proscript.get_last_word().end_time == -1:
			diff = word.start_time - proscript.get_last_word().end_time
		else: 
			diff = 0.0
		word.pause_before = float(FLOAT_FORMATTING.format(diff))
		if not proscript.get_last_word() == None: proscript.get_last_word().pause_after = word.pause_before 

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
		f0_contour = np.array(word_id_to_raw_f0_features_dic[word_id])  #this is two dimensional
		i0_contour = np.array(word_id_to_raw_i0_features_dic[word_id])  #this is two dimensional
		
		word.contour_xaxis = f0_contour[:,0].tolist() if f0_contour.size else []
		word.f0_contour = f0_contour[:,1].tolist() if f0_contour.size else []
		word.i0_contour = i0_contour[:,1].tolist() if i0_contour.size else []

		#punctuation
		#...
		proscript.add_word(word)
	
	return proscript

def featureVectorToFloat(featureVector):
	features_fixed = [0.0] * len(featureVector)
	for ind, val in enumerate(featureVector):
		if val == 'NA':
			features_fixed[ind] = 0.0
		else:
			features_fixed[ind] = float(FLOAT_FORMATTING.format(float(val)))
	return features_fixed

#--vvv--File access helper functions--vvv--
def findAggsFile(working_directory, feat):
	feat_dir = os.path.join(working_directory, feat)
	if os.path.exists(feat_dir):
		for file in os.listdir(feat_dir):
			if file.endswith("aggs.txt"):
				return os.path.join(working_directory, feat, file)
	sys.exit("Cannot find %s aggs file"%feat)

def checkFile(filename, variable):
    if not filename:
        sys.exit("%s file not given"%variable)
    else:
        if not os.path.isfile(filename):
            sys.exit("%s file %s does not exist"%(variable, filename))

def checkFolder(dir, variable):
	if not os.path.exists(dir):
		sys.exit("%s directory not given"%variable)
#--^^^--File access helper functions--^^^--

def main(options):
	checkFolder(options.dir_working, "dir_working")
	checkFile(options.file_wordalign, "file_wordalign")

	file_wordaggs_f0 = findAggsFile(options.dir_working, "f0")
	file_wordaggs_i0 = findAggsFile(options.dir_working, "i0")

	dir_raw_f0 = os.path.join(options.dir_working, "raw-f0")
	dir_raw_i0 = os.path.join(options.dir_working, "raw-i0")

	[word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic] = readTedDataToMemory(options.file_wordalign, file_wordaggs_f0, file_wordaggs_i0, dir_raw_f0, dir_raw_i0)
	proscript = structureData(word_id_to_f0_features_dic, word_id_to_i0_features_dic, word_data_aligned_dic, word_id_to_raw_f0_features_dic, word_id_to_raw_i0_features_dic)

	dir_proscript = os.path.join(options.dir_working, "proscript")
	if not os.path.exists(dir_proscript):
		os.makedirs(dir_proscript)

	if options.id_file:
		full_proscript_filename = "%s.proscript.csv"%options.id_file
		lite_proscript_filename = "%s.litescript.csv"%options.id_file
	else:
		full_proscript_filename = "proscript.csv"
		lite_proscript_filename = "litescript.csv"
	full_proscript_filename = os.path.join(dir_proscript, full_proscript_filename)
	lite_proscript_filename = os.path.join(dir_proscript, lite_proscript_filename)

	if options.feature_set:
		proscript.to_csv(lite_proscript_filename, ["word"] + options.feature_set)
	
	proscript.to_csv(full_proscript_filename)
	
	return 1

if __name__ == "__main__":
	usage = "usage: %prog [-s infile] [option]"
	parser = OptionParser(usage=usage)
	parser.add_option("-l", "--align", dest="file_wordalign", default=None, help="word.txt.norm.align", type="string")	#in /txt-sent
	parser.add_option("-d", "--dir_working", dest="dir_working", default=None, help="Working directory where prosodic parameters and output is stored", type="string")
	parser.add_option("-i", "--id", dest="id_file", default="proscript", help="optional file id", type="string")
	parser.add_option("-f", "--feature_set", dest="feature_set", help="feature set to extract in output proscript file", default=[], type="string", action='append')

	(options, args) = parser.parse_args()

	print("=====Proscripter=====")
	
	if main(options):
		print("Proscripted.")
	else:
		print("Failed.")
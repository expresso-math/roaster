## ================ GRINDER.PY ================
## Class encapsulating a Neural Network,
## Data Set, and various methods for
## manipulating them and utilizing them.
##
## Developed by: Josef Lange & Daniel Guilak

## PyBrain Imports
from pybrain.tools.shortcuts import buildNetwork
from pybrain.supervised.trainers import BackpropTrainer
from pybrain.datasets import SupervisedDataSet

## NumPy Imports
import numpy

## Imaging Imports
from PIL import Image

## Python Core Imports
import os, fileinput, md5, datetime, socket

## Settings
hostname = socket.gethostname()

OCRN_PATH = "/home/dg/Ocrn"

if hostname == "Plutonium":
	OCRN_PATH = "/Users/josefdlange/Projects/Expresso/roaster/"

class Grinder:
	"""
	Class described at top of grinder.py
	"""
	def __init__(self):
		### Neural Network Initialization
		self.neural_network = buildNetwork(100,80,1)
		self.input_dimension = 100
		self.output_dimension = 1
		self.neural_network.sortModules()
		### Data Set Initialization
		self.data_set = SupervisedDataSet(self.input_dimension, self.output_dimension)
		### Trainer initialization for the sake of being there.
		self.trainer = None

	def load_data(self, file_path=[OCRN_PATH + 'data/inputdata']):
		for line in fileinput.input(file_path):
			x = line.split(':')
			self.data_set.appendLinked(self.get_feature_vector(x[0]), numpy.array([int(x[1])]))
			self.trainer = BackpropTrainer(self.neural_network, self.data_set, learningrate=0.1, verbose = True)

	def get_feature_vector(self, image_path):
		array = self.get_normalized_image_array(image_path)
		vector = numpy.resize(array, (1,100))
		return vector[0]

	def get_normalized_image_array(self, image_path):
		image_array = self.get_image_array(image_path)
		return self.get_normalized_array(image_array)

	def get_image_array(self, image_path):
		try:
			image = Image.open(image_path).convert("1")
			image_array = numpy.asarray(image.crop(image.getbbox()).resize((10,10))).astype(float)
			x = numpy.clip(image_array, 0, 1)
			return x
		except IOError:
			print "Image File Not Found!"
			return numpy.zeros((10,10))

	def get_normalized_array(self, image_array):
		non_zero_cells = numpy.transpose(image_array.nonzero())
		for i in range (0, non_zero_cells.shape[0]):
			self.normalize_array_cell(image_array, non_zero_cells[i][0], non_zero_cells[i][1])
		return image_array

	def normalize_array_cell(self, array, x, y):
		for c in range(1,5):
			for i in range(x-c, x+c+1):
				for j in range(y-c, y+c+1):
					if i <= 9 and i >= 0 and j <= 9 and j >= 0:
						if array[i,j] < array[x,y] and array[i,j] < array[x,y] - 0.2*c:
							array[i,j] = array[x,y] - 0.2*c

	def train(self, max_epochs = 100, is_verbose = True):
		if self.trainer:
			self.trainer.trainUntilConvergence(maxEpochs = max_epochs, verbose = is_verbose, continueEpochs = 100, validationProportion = 0.25)

	def guess(self, image_file_path):
		if image_file_path:
			vector = self.get_feature_vector(image_file_path)
			result = self.neural_network.activate(vector)
			print "RESULT IS" + str(round(result[0],0))
			return str(unichr(int(round(result[0],0))))

	def guess_on_image_buffer(self, image_buffer):
		image = Image.open(image_buffer)
		pathname = OCRN_PATH+"/data/testdata/" + md5.new(str(datetime.datetime.now())).hexdigest() + ".bmp"
		tempImage = image.convert("1")
		tempImage.save(pathname, "BMP")
		result = self.guess(pathname)
		return result

	def add_data(self, image_tuple):
		"""
		Takes a tuple of (imageData, asciiVal) and adds all images to
		../data/trainingdata/ and then adds a line to imagedata
		"""
		image_data, ascii_value = image_tuple
		
		# For each imageData entry in the imageData list, save as a bmp and
		# write that path to imageData with `path:asciiVal`

		#This is to not have to do a getTrainingCount call every time.
		train_count = self.training_count()
		data_file = open(OCRN_PATH+"/data/inputdata", "a")

		for image in image_data:
			path_name = OCRN_PATH+"/data/trainingdata/" + str(train_count) + ".bmp"
			temp_image = image.convert("1")
			temp_image.save(path_name, "BMP")
			data_file.write(path_name+":"+str(ascii_value)+"\n")
			train_count = train_count + 1 
		
		data_file.close()

	def training_count(self):
		"""
		Gets the number of trained images from the imageData file.
		"""
		# Will need to change this to relative path later.
		wcData = os.popen("wc -l " + OCRN_PATH + "/data/inputdata").read()
		# Because wc returns number and filename
		wcList = wcData.split()
		if not wcList:
			wcList = ['0']
		print "wcList is " + str(wcList)
		return int(wcList[0])

	def reset(self):
		self.neural_network = buildNetwork(100, 80, 1)
		self.neural_network.sortModules()
		self.data_set = SupervisedDataSet(self.input_dimension, self.output_dimension)

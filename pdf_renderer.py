from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot
from scipy.misc import imread
from os import path
import numpy

# approach to pdf making based on: https://stackoverflow.com/questions/2252726/how-to-create-pdf-files-in-python
# TODO: shouldn't be using pyplot in OOP

class PdfRenderer():

	# columns,rows of cards on the page
	card_grid = (3,3)

	# the dimensions of the page and cards to use, in inches
	page_size = (8.5,11)
	card_size = (2.5,3.5)

	# TODO: PdfPages doesn't need to be created yet
	def __init__(self, path : str):

		self.pp = PdfPages(path) 
		self.i = 1


	def _plot_image(self, image):

		pyplot.imshow(image, aspect='equal')
		a = pyplot.gca()
		a.get_xaxis().set_visible(False)
		a.get_yaxis().set_visible(False)

	
	def add(self, image):

		pyplot.subplot(*self.card_grid, self.i)
		self._plot_image(image)
		self.i += 1

	# returns the (horizontal,vertical) margin widths of the page
	#   as defined by what configuration of cards of what size on a page of what size
	# TODO: this code is repetative
	def get_margins(self):
		content_size = tuple ( (size * self.card_grid[i])/self.page_size[i] for i,size in enumerate(self.card_size) )
		print(content_size)
		return tuple( (1-i)/2 for i in content_size )

	# writes all cards thusfar collected to pdf
	def save(self):

		pyplot.gcf().set_size_inches(*self.page_size)
		margins = self.get_margins()
		pyplot.subplots_adjust(left=margins[0], right=1-margins[0], top=1-margins[1], bottom=margins[1], wspace=0, hspace=0)
		self.pp.savefig(pyplot.gcf())
		self.pp.close()


	# for 'with' statements
	def __enter__(self):
		# TODO: in theory pp should be created here...
		pass

	def __exit__(self):

		self.save()
	
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib import pyplot
from scipy.misc import imread
from os import path
import numpy

# approach to pdf making based on: https://stackoverflow.com/questions/2252726/how-to-create-pdf-files-in-python
# TODO: shouldn't be using pyplot in OOP

class PdfRenderer():

    # rows/columns of cards on the page
    rows = 3
    columns = 3

    def __init__(self, path : str):

        self.pp = PdfPages(path) 
        self.i = 1


    def _plot_image(self, image):

        pyplot.imshow(image)
        a = pyplot.gca()
        a.get_xaxis().set_visible(False)
        a.get_yaxis().set_visible(False)

    
    def add(self, image):

        pyplot.subplot(self.rows, self.columns, self.i)
        self._plot_image(image)
        self.i += 1


    # writes all cards thusfar collected to pdf
    def save(self):

        self.pp.savefig(pyplot.gcf())
        self.pp.close()


    # for 'with' statements
    def __enter__(self):
        # TODO: in theory pp should be created here...
        pass

    def __exit__(self):

        self.save()
    
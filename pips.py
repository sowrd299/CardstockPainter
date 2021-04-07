from PIL import Image

# a class to represent a line of pips on a card
class Pips():

	# takes: 
	#   the position of the first pip
	#   the step to each pip after that
	#   the kinds of pips in the set, and when to render them
	#   the condition when it knows it is on its last pip
	def __init__(self, pos : (int, int), step : (int, int), pips : [("card,i=>bool", Image.Image)], end_when : ("card,i=>bool")):
		self.pos = pos
		self.step = step
		self.pips = pips
		self.end_when = end_when

	# draws pips onto the image, according to the given card's stats
	def render(self, img : Image.Image, card : dict):

		# walk through the indexes of pips
		pos = self.pos
		i = 1
		while not self.end_when(card, i):

			#render all applicable pips at the index
			for render_if, symbol in self.pips:
				if render_if(card, i):
					img.paste(symbol, pos)
			
			pos = (pos[0] + self.step[0], pos[1] + self.step[1])
			i += 1
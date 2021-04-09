from PIL import Image

from .frame_element import FrameElement

# a class to represent a line of pips on a card
class Pips(FrameElement):

	# takes: 
	#   the position of the first pip
	#   the step to each pip after that
	#   the kinds of pips in the set, and when to render them
	#   the condition when it knows it is on its last pip
	# TODO: Pip could be a recursive frame element... maybe...
	def __init__(self, pos : (int, int), step : (int, int), pips : [("card,i=>bool", Image.Image)], continue_while : ("card,i=>bool"), **kwargs):
		super().__init__(pos=pos, **kwargs)
		self.step = step
		self.pips = pips
		self.continue_while = continue_while

	# draws pips onto the image, according to the given card's stats
	def _render(self, img : Image.Image, card : dict):

		# walk through the indexes of pips
		pos = (0,0)
		i = 1
		while self.continue_while(card, i):

			#render all applicable pips at the index
			for render_if, symbol in self.pips:
				if render_if(card, i):
					img.paste(symbol, pos)
			
			pos = (pos[0] + self.step[0], pos[1] + self.step[1])
			i += 1
from PIL import Image

# a super class for everything that gets drawn onto the card
class FrameElement():

	def __init__(self, render_if = lambda x : True, pos = (0,0), width=500, rotation = 0):
		self.render_if = render_if
		self.pos = pos
		self.width = width
		self.rotation = rotation 

	def _render(self):
		raise NotImplementedError

	def render(self, cardImg : Image.Image, card : dict):

		if self.render_if(card):
			img = Image.new("RGBA", (self.width, self.width))

			self._render(img, card)

			rotImg = img.rotate(self.rotation)
			cardImg.paste( rotImg, self.pos)
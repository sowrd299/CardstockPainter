from PIL import Image, ImageDraw, ImageTk
from .text_box import TextBox
from .pips import Pips
from .frame_element import FrameElement
from card_data import CardData

#returns fields derived from extant fields
def get_derived_fields(item : dict, derived_fields : {str : "card => value"}):
	r = dict()
	for field, func in derived_fields.items():
		r[field] = func(item)
	return r

# a class to define a card frame layout
class Frame():

	# exists to abstract away pillow
	class RenderedCard():
		def __init__(self, img):
			self.img = img
		def save(self, file):
			img = self.img
			if ".jpg" in file:
				img = img.convert("RGB")
			img.save(file)
		def get_image(self):
			return self.img
		def get_tk_photoimage(self):
			return ImageTk.PhotoImage(self.img)


	# defaults
	boarder_color = (0,0,0)
	boarder_width = 8
	bg_color = (255, 255, 255)

	def __init__(self,
			boxes : [FrameElement] = [],
			derived_fields : {str : "card => value"} = dict(),
			size : (int, int) = (225,315),
	):
		self.boxes = boxes 
		self.derived_fields = derived_fields
		self.size = size

	# returns the size of the frame excluding the boarder
	def get_inner_size(self):
		return tuple(i - 2*(self.boarder_width-1) for i in self.size)


	# returns a new blank image of appropriate size for the frame
	#	 fills the image with the specified color, defaults to clear
	#		 ...(clear shader magenta for error detection)
	def _new_blank_image(self, color = (255,255,0,0)):
		return Image.new('RGBA', self.size, color = color)

	# composites two given layers of the card
	# assumes the base layer is already correctly formated for this frame
	#   ... e.g. was created by _new_blank_image
	def _composite(self, top_layer : Image.Image, base_layer : Image.Image, offset : (int, int) = (0,0)):
		img = top_layer
		if top_layer.size != self.size or top_layer.mode != 'RGBA':
			img = self._new_blank_image()
			img.paste(top_layer, offset)
		return Image.composite(img, base_layer, img)

	# renders the given data in this frame
	def render(self, card : dict):

		# setup the image
		img = self._new_blank_image(self.boarder_color)

		# setup the card
		# TODO: Derived fields might make more sense in CardData...
		df = get_derived_fields(card, self.derived_fields)
		derived_card = CardData(card, **df)

		# create the boarder (by subtraction)
		# TODO: consider moving this to it's own class
		draw = ImageDraw.Draw(img)
		intern_rect =[(self.boarder_width, self.boarder_width), (self.size[0]-self.boarder_width, self.size[1]-self.boarder_width)] 
		draw.rectangle(intern_rect, fill=self.bg_color)

		# draw the text boxes and pips
		for box in self.boxes:
			text_layer = self._new_blank_image()
			box.render(text_layer, derived_card)
			img = self._composite(text_layer, img)

		return self.RenderedCard(img)
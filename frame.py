from PIL import Image, ImageDraw
from text_box import TextBox

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
            self.img.save(file)

    # defaults
    size = (225,315)
    boarder_color = (0,0,0)
    boarder_width = 8
    bg_color = (255, 255, 255)

    def __init__(self, boxes : {str : TextBox}, derived_fields : {str : "card => value"}):
        self.boxes = boxes
        self.derived_fields = derived_fields

    # renders the given data in this frame
    def render(self, card : dict):

        # setup the image
        img = Image.new('RGBA', self.size, color = self.boarder_color)
        draw = ImageDraw.Draw(img)

        # setup the card
        df = get_derived_fields(card, self.derived_fields)
        fields = dict(card, **df)

        # create the boarder (by subtraction)
        # TODO: consider moving this to it's own class
        intern_rect =[(self.boarder_width, self.boarder_width), (self.size[0]-self.boarder_width, self.size[1]-self.boarder_width)] 
        draw.rectangle(intern_rect, fill=self.bg_color)

        # draw the text boxes
        for name,box in self.boxes.items():
            box.render(img, fields[name])

        return self.RenderedCard(img)
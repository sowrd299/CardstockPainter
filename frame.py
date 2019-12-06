from PIL import Image, ImageDraw
from xml.etree import ElementTree
from text_box import TextBox
from os import path

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


    # creates a new frame, as defined by the given xml file
    # TODO: handle getting data in different forms
    # TODO: break this into multiple methods like a civilized programmer
    @staticmethod
    def open_from_xml(file_path : str):

        frame = Frame(None, None)

        tree = ElementTree.parse(file_path)
        root = tree.getroot()

        # create derived fields
        derived_fields = dict()
        for derived_field in root.iter("derived_field"):
            derived_fields[derived_field.attrib["name"]] = lambda card : eval(derived_field.attrib["eq"].format(**card))

        # create symbol sets
        symbol_sets = dict()
        for symbol_set in root.iter("symbol_set"):

            # setup image loading
            directory = symbol_set.attrib["dir"]
            open_sym = lambda file : Image.open(path.join(directory, file))

            # build the symbol set
            #   using itter instead of find allows for symbol super and subsets to function automatically (though not efficiently)
            symbol_sets[ symbol_set.attrib["name"] ] = { sym.attrib["name"] : open_sym(sym.attrib["file"]) for sym in symbol_set.iter("symbol") }

        # create text boxes
        text_boxes = dict()
        frame_vars = { "w" : frame.size[0], "h" : frame.size[1], "bw" : frame.boarder_width }
        eval_vars = lambda s : eval(s.format(**frame_vars))
        for box in root.iter("text_box"):
            text_boxes[ box.attrib["name"] ] = TextBox(
                    (eval_vars(box.attrib["x"]), eval_vars(box.attrib["y"])),
                    eval_vars(box.attrib["w"]),
                    symbol_sets[box.attrib["symbols"]]
            )

        frame.boxes = text_boxes
        frame.derived_fields = derived_fields

        return frame


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
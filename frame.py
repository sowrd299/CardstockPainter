from PIL import Image, ImageDraw
from text_box import TextBox
from pips import Pips

# for handling XML loading
from xml.etree import ElementTree
from os import path
import re

# part of XML handling
# a place for cashing regex expected to be seen often
known_regex = dict()

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

    def __init__(self,
            frame_layers : [("card => bool", Image.Image)] = [],
            boxes : {str : TextBox} = dict(),
            derived_fields : {str : "card => value"} = dict(),
            pips : {str : Pips} = dict() ):

        self.frame_layers = frame_layers
        self.boxes = boxes 
        self.derived_fields = derived_fields
        self.pips = pips

    # returns the size of the frame excluding the boarder
    def get_inner_size(self):
        return tuple(i - 2*(self.boarder_width-1) for i in self.size)

    # creates a new frame, as defined by the given xml file
    # TODO: handle getting XML data in different forms
    # TODO: break this into multiple methods like a civilized programmer
    # TODO: all these nest methods can't be efficient
    # TODO: also maybe this whole thing should just be its own file
    @staticmethod
    def open_from_xml(file_path : str):

        # evaluates a parameterized field of a card
        def eval_card_field(field_value : str, card : dict, **args ):

            def regex_matches(regex, text):
                global known_regex
                compiled_regex = None
                if regex in known_regex:
                    compiled_regex = known_regex[regex]
                else:
                    compiled_regex = re.compile(regex)
                    known_regex[regex] = compiled_regex
                return compiled_regex.search(text)
                
            context = card
            if args:
                context = dict(card, **args)

            r = eval(field_value.replace("'","'''").format(**context))
            return r

        # setups the frame
        frame = Frame()

        # evaluates a peramiterized field of a pixel measurement
        def eval_pixel_field(value : str, frame_vars = { "w" : frame.size[0], "h" : frame.size[1], "bw" : frame.boarder_width } ):
            return int(eval(value.format(**frame_vars)))

        # opens the xml
        tree = ElementTree.parse(file_path)
        root = tree.getroot()

        # create frame layers
        frame_layers = []
        directory = root.attrib["layer_dir"]
        open_layer = lambda file : Image.open(path.expanduser(path.join(directory, file))).resize( frame.get_inner_size() )
        for frame_layer in root.iter("frame_layer"):
            render_if = lambda card, s=frame_layer.attrib["render_if"] : eval_card_field(s, card)
            frame_layers.append( (render_if, open_layer(frame_layer.attrib["file"])) )

        # create derived fields
        derived_fields = dict()
        for derived_field in root.iter("derived_field"):
            derived_fields[derived_field.attrib["name"]] = lambda card, s=derived_field.attrib["eq"] : eval_card_field(s, card)
            # NOTE: need to use extra value in agrument to capture value instead of variable

        # create symbol sets
        symbol_sets = dict()
        for symbol_set in root.iter("symbol_set"):

            # setup image loading
            directory = symbol_set.attrib["dir"]
            open_sym = lambda file : Image.open(path.expanduser(path.join(directory, file)))

            # build the symbol set
            #   using itter instead of find allows for symbol super and subsets to function automatically (though not efficiently)
            symbol_sets[ symbol_set.attrib["name"] ] = { sym.attrib["name"] : open_sym(sym.attrib["file"]) for sym in symbol_set.iter("symbol") }

        # create text boxes
        text_boxes = dict()
        for box in root.iter("text_box"):
            text_boxes[ box.attrib["name"] ] = TextBox(
                    (eval_pixel_field(box.attrib["x"]), eval_pixel_field(box.attrib["y"])),
                    eval_pixel_field(box.attrib["w"]),
                    symbol_sets[box.attrib["symbols"]] if ("symbols" in box.attrib) else dict()
            )

        # create pips; also deal the fun the is naming a class in the plural
        pipses = dict()
        for pips in root.iter("pips"):

            symbol_set = symbol_sets[pips.attrib["symbol_set"]]

            # add each pip symbol
            ps = []
            for pip in pips.iter("pip"):
                ps.append( (
                    lambda card, i, s=pip.attrib["render_if"] : eval_card_field(s,card,i=i),
                    symbol_set[pip.attrib["symbol"]]
                ) )

            # build the pips object
            pipses[ pips.attrib["name"] ] = Pips(
                (eval_pixel_field(pips.attrib["x"]), eval_pixel_field(pips.attrib["y"])),
                (eval_pixel_field(pips.attrib["x_step"]) if "x_step" in pips.attrib else 0,
                eval_pixel_field(pips.attrib["y_step"]) if "y_step" in pips.attrib else 0),
                ps,
                lambda card, i, s=pips.attrib["end_when"] : eval_card_field(s,card,i=i)
            )

        # assemble the frame and cleanup
        frame.frame_layers = frame_layers
        frame.boxes = text_boxes
        frame.derived_fields = derived_fields
        frame.pips = pipses

        return frame

    # returns a new blank image of appropriate size for the frame
    #     fills the image with the specified color, defaults to clear
    #         ...(clear shader magenta for error detection)
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
        df = get_derived_fields(card, self.derived_fields)
        fields = dict(card, **df)

        # create the boarder (by subtraction)
        # TODO: consider moving this to it's own class
        draw = ImageDraw.Draw(img)
        intern_rect =[(self.boarder_width, self.boarder_width), (self.size[0]-self.boarder_width, self.size[1]-self.boarder_width)] 
        draw.rectangle(intern_rect, fill=self.bg_color)

        # draw frame layers
        for render_if,layer in self.frame_layers:
            if render_if(card):
                #print("Rendering frame layer") # TODO: Testing
                img = self._composite( layer, img, (self.boarder_width, self.boarder_width) )

        # draw the text boxes and pips
        text_layer = self._new_blank_image()
        for name,box in self.boxes.items():
            box.render(text_layer, fields[name])
        for name,pips in self.pips.items():
            pips.render(text_layer, card) 
        img = self._composite(text_layer, img)

        return self.RenderedCard(img)
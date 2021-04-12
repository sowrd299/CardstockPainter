from tools import EMPTY, is_eval_dangerous, make_eval_safe

from PIL import Image, ImageDraw, ImageTk

from frame.frame import Frame
from frame.text_box import TextBox
from frame.pips import Pips
from frame.frame_layer import FrameLayer

# for handling XML loading
from xml.etree import ElementTree
from os import path


# a class for deriving values from raw input data
class DerivedAttrib():

    def __init__(self, output, function, inputs=None, default=None):
        self.output = output
        self.function = function
        self.inputs = inputs if inputs != None else (output,) # defaults to having the same input and output
        self.default = default if isinstance(default, DerivedAttrib) or default==None else ConstAttrib(output, default)

    # will only derive the value if all inputs are present, and atleast one
    #   ...input was updated since the inherited data
    def derive(self, data, updated_attribs=set()):
        if all(i in data for i in self.inputs) and ((not updated_attribs) or (not (self.output in data)) or any(i in updated_attribs for i in self.inputs)):
            data[self.output] = self.function(*(data[i] for i in self.inputs))
        elif self.default:
            self.default.derive(data, updated_attribs)

# a "derived" value that is always the same
class ConstAttrib(DerivedAttrib):
    def __init__(self, output, constant):
        super().__init__(output, (lambda *args, c=constant : c), tuple())


# Parses attributes from XML into a dictionary
# Includes evaluating some variables and inheritence
def parse_attribs(nodes, node, derived_attribs : [DerivedAttrib]):
    # the element to inherit from
    inherit = dict()
    for k in ("inherit", "type_setting"):
        if k in node.attrib:
            try:
                inherit.update(nodes[node.attrib[k]])
            except KeyError as e:
                print('Invalid "{}"; Element "{}" does not exist!'.format(k, node.attrib[k]))

    # copy the various settings
    d = dict(inherit)
    for attrib, val in node.attrib.items():
        d[attrib] = val
    # format settings
    for da in derived_attribs:
        try:
            da.derive(d, node.attrib)
        except Exception as e:
            print("Error in derivation of field {}".format(da.output))
            raise e

    # cleanup 
    if "name" in node.attrib:
        nodes[node.attrib["name"]] = d
    return d


def create_derived_fields(elements):
    # create derived fields
    derived_fields = dict()
    for derived_field in elements:
        derived_fields[derived_field.attrib["name"]] = lambda card, s=derived_field.attrib["eq"] : card.eval_card_field(s)
        # NOTE: need to use extra value in agrument to capture value instead of variable
    return derived_fields


def create_symbol_sets(elements):
    symbol_sets = dict()
    for symbol_set in elements:

        # setup image loading
        directory = symbol_set.attrib["dir"]
        open_sym = lambda file : Image.open(path.expanduser(path.join(directory, file)))

        # build the symbol set
        #   using itter instead of find allows for symbol super and subsets to function automatically (though not efficiently)
        symbol_sets[ symbol_set.attrib["name"] ] = { sym.attrib["name"] : open_sym(sym.attrib["file"]) for sym in symbol_set.iter("symbol") }
    return symbol_sets


# creates a new frame, as defined by the given xml file
# TODO: handle getting XML data in different forms
# TODO: break this into multiple methods like a civilized programmer
# TODO: all these nest methods can't be efficient
def frame_from(file_path : str):

    # opens the xml
    tree = ElementTree.parse(file_path)
    root = tree.getroot()

    # sets the frame up
    frame = Frame(size=(int(root.attrib["width"]), int(root.attrib["height"])))
    
    # invarient elements; todo: maybe these too should use parse attribs...
    derived_fields = create_derived_fields(root.iter("derived_field"))
    symbol_sets = create_symbol_sets(root.iter("symbol_set"))

    # frame elements
    element_attribs = dict()
    boxes = []

    # evaluates a peramiterized field of a pixel measurement
    def eval_pixel_field(value : str, frame_vars = { "w" : frame.size[0], "h" : frame.size[1], "bw" : frame.boarder_width } ):
        r = eval(value.format(**frame_vars))
        if isinstance(r, float):
            r = int(r)
        if isinstance(r, tuple):
            r = tuple(int(i) for i in r)
        return r

    # opens a layer image file
    directory = root.attrib["layer_dir"]
    open_layer = lambda file : Image.open(path.expanduser(path.join(directory, file))).resize( frame.get_inner_size() )

    # determines if a frame element should be rendered on the card
    render_if = lambda render_if : (lambda card, p=render_if : card.eval_card_field(p))

    # gets the text a text box should render
    render_text = lambda field : (lambda card, s = field : card.eval_card_field(s))

    # attributes of frame elements that must be derived from the raw data
    derived_attribs = [
        DerivedAttrib("size", eval_pixel_field),
        DerivedAttrib("line_spacing", eval_pixel_field),
        DerivedAttrib("color", eval_pixel_field),
        DerivedAttrib("rotation", eval_pixel_field),
        DerivedAttrib("layer", open_layer, ("file",)),
        DerivedAttrib("render_if", render_if),
    ]

    box_derived_attribs = [
        DerivedAttrib("x", eval_pixel_field),
        DerivedAttrib("y", eval_pixel_field),
        DerivedAttrib("pos", (lambda x, y: (x,y)), ("x","y")),
        DerivedAttrib("symbol_set", lambda k : symbol_sets[k],
            default= dict()
        ),
        # text box specific
        DerivedAttrib("width", eval_pixel_field, ("w",)),
        DerivedAttrib("render_text", render_text,
            default = DerivedAttrib("render_text", lambda name : render_text("'{{{0}}}'".format(name)), ("name",)), 
        ),
        # pips specific
        DerivedAttrib("x_step", eval_pixel_field,
            default= 0
        ),
        DerivedAttrib("y_step", eval_pixel_field,
            default= 0
        ),
        DerivedAttrib("step", (lambda x, y: (x,y)), ("x_step","y_step")),
        DerivedAttrib("continue_while", lambda continue_while : (lambda card, i, p=continue_while : card.eval_card_field(p, i=i)) ),
    ]

    # create frame layers
    for frame_layer in root.iter("frame_layer"):
        try:
            attribs = parse_attribs(element_attribs, frame_layer, derived_attribs)
            boxes.append(FrameLayer(pos=(frame.boarder_width, frame.boarder_width), **attribs))
        except FileNotFoundError as e:
            print('Layer image "{}" could not be found!'.format(frame_layer.attrib["file"]))

    # create type setting presets (these are treated as frame elements so that they can be inherited from)
    for type_setting in root.iter("type_setting"):
        parse_attribs(element_attribs, type_setting, derived_attribs)

    # create text boxes
    for box in root.iter("text_box"):

        styles = []
        for style in box.iter("text_style"):
            styles.append( (style.attrib["type"], lambda card, s=style.attrib["range"] : card.eval_card_field(s)))
        
        boxes.append( TextBox( styles = styles, **parse_attribs(element_attribs, box, derived_attribs+box_derived_attribs)) )

    # create pips; also deal with the fun the is naming a class in the plural
    for pips in root.iter("pips"):
        attribs = parse_attribs(element_attribs, pips, derived_attribs + box_derived_attribs)
        symbol_set = attribs["symbol_set"]
        # add each pip symbol
        ps = []
        for pip in pips.iter("pip"):
            ps.append( (
                lambda card, i, s=pip.attrib["render_if"] : card.eval_card_field(s,i=i),
                symbol_set[pip.attrib["symbol"]]
            ) )
        # build the pips object
        boxes.append( Pips( pips = ps, **attribs ) )

    # assemble the frame and cleanup
    frame.boxes = boxes
    frame.derived_fields = derived_fields

    return frame
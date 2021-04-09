from tools import EMPTY, is_eval_dangerous, make_eval_safe

from PIL import Image, ImageDraw, ImageTk

from frame.frame import Frame
from frame.text_box import TextBox
from frame.pips import Pips
from frame.frame_layer import FrameLayer

# for handling XML loading
from xml.etree import ElementTree
from os import path
import re

# part of XML handling
# a place for cashing regex expected to be seen often
known_regex = dict()


# evaluates a parameterized field of a card
# TODO: This *might* want to be its own thing? or at least the part getting stuff from dicts
def eval_card_field(field_value : str, card : dict, **args ):

    # HERE ARE THE FUNCTIONS  CALLABLE FROM CARD FIELDS

    def indexes_of(matches):
        if matches:
            return [(match.start(), match.end()) for match in matches]
        else:
            return None

    def regex_matches(regex, text):
        global known_regex
        compiled_regex = None
        if regex in known_regex:
            compiled_regex = known_regex[regex]
        else:
            compiled_regex = re.compile(regex)
            known_regex[regex] = compiled_regex
        matches = []
        pos = 0
        while True:
            match = compiled_regex.search(text, pos)
            if match:
                matches.append(match)
                pos = match.end()
            else:
                return matches

    All = (0,-1)
        
    # Assemble the context, evaluate and return

    context = card
    if args:
        context = dict(card, **args)

    r = ""
    try:
        r = eval(field_value.replace("'","'''").format(**context))
    # Errors in {Var}'s being used
    except KeyError as e:
        print('Failed to find key "{}" in context, treating as empty...'.format(e))
        context[eval(str(e))] = EMPTY # NOTE: This is a weird trick for finding the failed key...
        return eval_card_field(field_value, context)
    # Errors in python syntax there-after
    except (SyntaxError, TypeError, NameError) as e:
        
        # Handle correcting for eval-dangerous without a fuss
        if any(map(is_eval_dangerous, context.values())): 
            return eval_card_field(field_value, { k:make_eval_safe(v) for k,v in context.items() })

        print('Illegal syntax in field "{}", evalling as "{}"!'.format(field_value, field_value.replace("'","'''").format(**context)))

    return r



# creates a new frame, as defined by the given xml file
# TODO: handle getting XML data in different forms
# TODO: break this into multiple methods like a civilized programmer
# TODO: all these nest methods can't be efficient
def frame_from(file_path : str):


    # opens the xml
    tree = ElementTree.parse(file_path)
    root = tree.getroot()

    # setups the frame
    frame = Frame(size=(int(root.attrib["width"]), int(root.attrib["height"])))
    boxes = dict()

    # evaluates a peramiterized field of a pixel measurement
    def eval_pixel_field(value : str, frame_vars = { "w" : frame.size[0], "h" : frame.size[1], "bw" : frame.boarder_width } ):
        r = eval(value.format(**frame_vars))
        if isinstance(r, float):
            r = int(r)
        if isinstance(r, tuple):
            r = tuple(int(i) for i in r)
        return r

    # create frame layers
    directory = root.attrib["layer_dir"]
    open_layer = lambda file : Image.open(path.expanduser(path.join(directory, file))).resize( frame.get_inner_size() )
    for frame_layer in root.iter("frame_layer"):
        render_if = lambda card, s=frame_layer.attrib["render_if"] : eval_card_field(s, card)
        try:
            file = frame_layer.attrib["file"]
            boxes[file] = FrameLayer(open_layer(file), render_if=render_if, pos=(frame.boarder_width, frame.boarder_width))
        except FileNotFoundError as e:
            print('Layer image "{}" could not be found!'.format(frame_layer.attrib["file"]))

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

    # create type setting presets
    type_settings = dict()
    for type_setting in root.iter("type_setting"):
        # the type setting to inherit from
        try:
            inherit = type_settings[type_setting.attrib["inherit"]] if "inherit" in type_setting.attrib else dict()
        except KeyError as e:
            print('Invalid type setting inheritence; Type setting "{}" does not exist!'.format(type_setting.attrib["inherit"]))
        # the various settings of the type setting
        d = dict()
        for setting in ["size", "line_spacing", "color", "font_file"]:
            if setting in type_setting.attrib:
                d[setting] = eval_pixel_field(type_setting.attrib[setting]) if setting != "font_file" else type_setting.attrib[setting]
            elif setting in inherit:
                d[setting] = inherit[setting]
        try:
            type_settings[type_setting.attrib["name"]] = d
        except KeyError as e:
            print('Invalid type setting; missing "name"!')
    print("Loaded type settings {}...".format(", ".join(type_settings)))

    # create text boxes
    for box in root.iter("text_box"):

        styles = []
        for style in box.iter("text_style"):
            styles.append( (style.attrib["type"], lambda card, s=style.attrib["range"] : eval_card_field(s, card)))
        
        type_setting = type_settings[box.attrib["type_setting"]] if "type_setting" in box.attrib else dict()

        rotation = 0
        if "rotation" in box.attrib:
            rotation = eval_pixel_field(box.attrib["rotation"])

        boxes[ box.attrib["name"] ] = TextBox(
                (eval_pixel_field(box.attrib["x"]), eval_pixel_field(box.attrib["y"])),
                eval_pixel_field(box.attrib["w"]),
                lambda card, s = box.attrib["render_text"] if "render_text" in box.attrib else "'{{{0}}}'".format(box.attrib["name"]) : eval_card_field(s, card),
                symbol_sets[box.attrib["symbols"]] if ("symbols" in box.attrib) else dict(),
                styles,
                rotation = rotation,
                **type_setting
        )

    # create pips; also deal with the fun the is naming a class in the plural
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
        boxes[ pips.attrib["name"] ] = Pips(
            (eval_pixel_field(pips.attrib["x"]), eval_pixel_field(pips.attrib["y"])),
            (eval_pixel_field(pips.attrib["x_step"]) if "x_step" in pips.attrib else 0,
            eval_pixel_field(pips.attrib["y_step"]) if "y_step" in pips.attrib else 0),
            ps,
            lambda card, i, s=pips.attrib["continue_while"] : eval_card_field(s,card,i=i)
        )

    # assemble the frame and cleanup
    frame.boxes = boxes
    frame.derived_fields = derived_fields

    return frame
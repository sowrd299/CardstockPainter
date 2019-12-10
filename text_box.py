from PIL import Image, ImageDraw, ImageFont
from tools import DictTree
from collections import defaultdict

# a class for rendering text data onto the card
class TextBox():

    # tracks changing indexies at strings are edited
    # allows code to reference consistent points accorss multiple versions
    # deals with "orignal indexes", indexes before any changes to the string were made
    class IndexMap():

        def __init__(self):
            self.map = defaultdict(int)

        # logs that the given original index (and all subsequence original indexes) position has moved by <shift>
        def add_shift(self, orig_i, shift):
            self.map[orig_i] += shift
            if self.map[orig_i] == 0:
                del self.map[orig_i]

        # returns the new index of the given character from the original string
        def get_shifted_index(self, orig_i):
            r = orig_i
            for i,s in self.map.items():
                if i <= orig_i:
                    r += s
            return r

    # defaults
    text_color = (0,0,0)
    line_spacing = 1
    font_file = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
    font_size = 11
    font = ImageFont.truetype(font_file, font_size)

    def __init__(self, pos : (int,int), width : int, render_text : "card => str",
            symbols : {str : Image.Image} = {}, styles : [(str,"card=>(int,int)")] = [],
            color = None, size = None, line_spaceing = None, font_file = None
    ):
        self.pos = pos
        self.width = width
        self.render_text = render_text
        self.symbols = DictTree(symbols)
        self.styles = styles # style describe when to bold, when to italicize

        if color:
            self.text_color = color

        if line_spaceing:
            self.line_spacing = line_spaceing

        if size or font_file:
            self.font = ImageFont.truetype(font_file or self.font_file, size or self.size)

    # returns (<the text with symbol codes removed>, {(<symbol index> : <symbol>})
    # TODO: add index mapping, and return symbols by original index
    def find_symbols(self, text):

        r_text = ""
        r_symbols = dict()

        i = 0 # index in original next
        while i < len(text):

            sub, sym = self.symbols.get_first_entry(text[i:])

            if sym:
                i += len(sub)
                r_text += "  " # TODO: handle non-square symbols
                r_symbols[len(r_text)] = sym
            
            else:
                r_text += text[i]
                i += 1

        return (r_text, r_symbols)


    # returns a wrapped version of the given text
    # TODO: this is the nieve implementation
    # TODO: implement automatically creeping down text size
    def wrap_text(self, draw : ImageDraw.Draw, text : str):

        index_map = self.IndexMap()

        wrapped_text = ""

        def under_width(ext = ''):
            return draw.multiline_textsize(wrapped_text + ext, self.font, self.line_spacing)[0] <= self.width

        for i in range(len(text)):
            c = text[i]
            len_added_chars = 0
            # actually keep building
            if under_width(c):
                wrapped_text += c
                '''
                elif text[i] == ' ':
                    # handle the case where spaces shouldn't start new lines
                    wrapped_text += "\n"
                '''
            else:
                # make room for the wrapping hyphen
                while not (under_width("-")):
                    cprime = wrapped_text[-1]
                    wrapped_text = wrapped_text[:-1]
                    c = cprime + c
                    i -= len(cprime) # allow i to continue tracking the first index in question
                # do not put spaces at the start of lines, and don't put dashes before them
                if c[0] == ' ':
                    wrapped_text += "\n"+c[1:]
                    len_added_chars = 1 
                else:
                    wrapped_text += "-\n" + c
                    len_added_chars = 2
                
                index_map.add_shift(i, len_added_chars)

        return (wrapped_text, index_map)

    # gets the pixel coordinate of the given index
    #   in the given text, after it would be drawn
    def get_coord_in_text(self, draw, text, index):
        # find the begining of the line the symbol in question is on
        line_start_index = index
        while line_start_index > 0 and text[line_start_index-1] != "\n":
            line_start_index -= 1
        # calc the coords
        x = draw.multiline_textsize(text[line_start_index:index], self.font, self.line_spacing)[0]
        y = draw.multiline_textsize(text[:line_start_index-1], self.font, self.line_spacing)[1] if line_start_index > 0 else 0
        return (x,y) 

    # emboldens the given range of the given text
    # indexes are inclusive , inclusive
    def embolden_text(self, draw, text, start_index, end_index):

        # apply (faux) bold; thinkens by one pixel and tripples alphas
        lines = text[start_index:end_index+(len(text) if end_index<0 else 0)+1].split("\n")
        i = start_index
        for line in lines:
            # for each line to bold, find that line
            offset = self.get_coord_in_text(draw, text, i)
            # apply the bold
            pos = (self.pos[0] + offset[0] + 1, self.pos[1] + offset[1])
            for j in range(3): # TODO: the dumbest way to do alpha reduction; not actually slow though
                draw.multiline_text(pos, line, fill=self.text_color, font=self.font, spacing=self.line_spacing)
            i += len(line) + 1


    # draw the given text onto the given box
    def render(self, img : Image.Image, card):

        # setup
        text = self.render_text(card)
        draw = ImageDraw.Draw(img)

        # processing
        symbol_text, symbols = self.find_symbols(text)
        wrapped_text, index_map_s_to_w = self.wrap_text(draw, symbol_text)

        # rendering, including faux bold
        # TODO: make a more robust faux bold that isn't all or nothing
        draw.multiline_text(self.pos, wrapped_text, fill=self.text_color, font=self.font, spacing=self.line_spacing)
        char_size = draw.textsize("W") # assumes capkkital W largest letter
        for index, symbol in symbols.items():
            symbol_size = ( int(char_size[1] * symbol.size[0] / symbol.size[0]) , char_size[1])
            s = symbol.resize(symbol_size)
            local_coords = self.get_coord_in_text(draw, wrapped_text, index_map_s_to_w.get_shifted_index(index)-1)
            img_coords = ( int(self.pos[0] + local_coords[0]), int(self.pos[1] + local_coords[1]) )
            img.paste( s,  img_coords )

        # apply styles
        for style,range_func in self.styles:
            index_ranges = range_func(card) # TODO: actually get the card to do this correctly
            if not index_ranges: # NOTE: enables styles to be scipped by returning False or None
                continue
            if style == "bold": # NOTE: "bold" term defined here
                for index_range in index_ranges if type(index_ranges[0]) == tuple else [index_ranges]: # supports getting a list of index ranges
                    self.embolden_text(draw, wrapped_text, *(index_map_s_to_w.get_shifted_index(i) for i in index_range))
from PIL import Image, ImageDraw
from tools import DictTree
import csv_loader

class TextBox():

    # defaults
    text_color = (0,0,0)

    def __init__(self, pos : (int,int), width : int, symbols : {str : Image.Image} ):
        self.pos = pos
        self.width = width
        self.symbols = DictTree(symbols)

    # returns (<the text with symbol codes removed>, {(<symbol index> : <symbol>})
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
        wrapped_text = ""

        def under_width(ext = ''):
            return draw.multiline_textsize(wrapped_text + ext)[0] <= self.width

        for i in range(len(text)):
            c = text[i]
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
                # do not put spaces at the start of lines, and don't put dashes before them
                if c[0] == ' ':
                    wrapped_text += "\n"+c[1:]
                else:
                    wrapped_text += "-\n" + c
        return wrapped_text

    # gets the pixel coordinate of the given index
    #   in the given text, after it would be drawn
    def get_coord_in_text(draw, text, index):


    # draw the given text onto the given box
    def render(self, draw : ImageDraw.Draw, text : str):
        # extract symbols
        symbol_text, symbols = self.find_symbols(text)
        # wrap the text
        wrapped_text = self.wrap_text(draw, symbol_text)
        # TODO: this is going to increase indexies...
        # draw the text
        draw.multiline_text(self.pos, wrapped_text, fill=self.text_color)
        # draw symbols
        for index, symbol in symbols.items():
            pass # TODO

# a class to define a card frame layout
class Frame():

    class RenderedCard():
        def __init__(self, img):
            self.img = img
        def save(self, file):
            self.img.save(file)

    # defaults
    size = (200,300)
    boarder_color = (0,0,0)
    boarder_width = 8
    bg_color = (255, 255, 255)

    def __init__(self, boxes : {str : TextBox}):
        self.boxes = boxes

    # renders the given data in this frame
    def render(self, card : dict):

        # setup
        img = Image.new('RGB', self.size, color = self.boarder_color)
        draw = ImageDraw.Draw(img)

        # create the boarder (by subtraction)
        # TODO: consider moving this to it's own class
        intern_rect =[(self.boarder_width, self.boarder_width), (self.size[0]-self.boarder_width, self.size[1]-self.boarder_width)] 
        draw.rectangle(intern_rect, fill=self.bg_color)

        # draw the text boxes
        for name,box in self.boxes.items():
            box.render(draw, card[name])

        # testing render 
        return self.RenderedCard(img)
        

if __name__ == "__main__":
    print("Starting...")

    # create derived fields
    derived_fields = dict()
    derived_fields["P/T"] = lambda card : "{0}/{1}".format(card["Power"], card["Toughness"]) if card["Power"] else ""

    # constants for creating the text boxes
    boxes = dict()
    bw = Frame.boarder_width
    size = Frame.size
    # the boxes themselves
    boxes["Name"] = TextBox((bw+8,bw+8), size[0]-bw*2-16)
    boxes["CMC"] = TextBox((bw+8, bw+32), size[0]-bw*2-16)
    boxes["Type"] = TextBox((bw+8, size[1]/3-32), size[0]-bw*2-16)
    boxes["Text"] = TextBox((bw+8, size[1]/3), size[0]-bw*2-16)
    boxes["P/T"] = TextBox((3*size[0]/4, size[1]-32), 3*size[0]/4-bw)

    symbols_paths = {
        "{W}" : "W.svg.png",
        "{U}" : "U.svg.png",
        "{B}" : "B.svg.png",
        "{R}" : "R.svg.png",
        "{G}" : "G.svg.png",
        "{T}" : "T.svg.png"
    }

    symbols = { s : Image.open(p) for s,p in symbols_paths.items() }

    # initialize the frame
    frame = Frame(boxes)

    # test CSV loader
    for card in csv_loader.cards_from("CardDesigns.csv"):
        csv_loader.pop_derived_fields(card, derived_fields)
        print(card) # testing
        rcard = frame.render(card)
        rcard.save("Output/"+card["Name"].replace(" ", "")+".png") 
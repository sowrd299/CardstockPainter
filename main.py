import csv_loader
from frame import Frame
from text_box import TextBox
from PIL import Image


if __name__ == "__main__":
    print("Starting...")

    # create derived fields
    derived_fields = dict()
    derived_fields["P/T"] = lambda card : "{0}/{1}".format(card["Power"], card["Toughness"]) if card["Power"] else ""

    # create the symbols
    symbols_paths = {
        "{W}" : "W.svg.png",
        "{U}" : "U.svg.png",
        "{B}" : "B.svg.png",
        "{R}" : "R.svg.png",
        "{G}" : "G.svg.png",
        "{T}" : "T.svg.png"
    }

    symbols = { s : Image.open("Symbols/" + p) for s,p in symbols_paths.items() }
    short_symbols = { s[1] : i for s,i in symbols.items() } # without the brackets

    # constants for creating the text boxes
    boxes = dict()
    bw = Frame.boarder_width
    size = Frame.size
    # the boxes themselves
    boxes["Name"] = TextBox((bw+8,bw+8), size[0]-bw*2-16, symbols)
    boxes["CMC"] = TextBox((bw+8, bw+32), size[0]-bw*2-16, short_symbols)
    boxes["Type"] = TextBox((bw+8, size[1]/3-32), size[0]-bw*2-16, symbols)
    boxes["Text"] = TextBox((bw+8, size[1]/3), size[0]-bw*2-16, symbols)
    boxes["P/T"] = TextBox((3*size[0]/4, size[1]-32), 3*size[0]/4-bw, symbols)

    # initialize the frame
    frame = Frame(boxes, derived_fields)

    # test CSV loader
    for card in csv_loader.cards_from("CardDesigns.csv"):
        print(card) # testing
        rcard = frame.render(card)
        rcard.save("Output/"+card["Name"].replace(" ", "")+".png") 
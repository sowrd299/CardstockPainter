from PIL import Image, ImageDraw
import csv_loader

class TextBox():

    # defaults
    text_color = (0,0,0)

    def __init__(self, pos : (int,int), width : int):
        self.pos = pos
        self.width = width

    # returns a wrapped version of the given text
    # TODO: this is the nieve implementation
    def wrap_text(self, draw : ImageDraw.Draw, text : str):
        wrapped_text = ""
        for i in range(len(text)):
            if draw.multiline_textsize(wrapped_text + text[i])[0] < self.width:
                wrapped_text += text[i]
            elif text[i] == ' ':
                # handle the case where spaces shouldn't start new lines
                wrapped_text += "\n"
            else:
                wrapped_text += "-\n" + text[i]
        return wrapped_text

    # draw the given text onto the given box
    def render(self, draw : ImageDraw.Draw, text : str):
        # wrap the text
        wrapped_text = self.wrap_text(draw, text)
        # draw the text
        draw.multiline_text(self.pos, wrapped_text, fill=self.text_color)

# a class to define a card frame layout
class Frame():

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
        img.save("test.png")

if __name__ == "__main__":
    print("Starting...")

    # create the text boxes
    boxes = dict()
    boxes["Name"] = TextBox((Frame.boarder_width+8,Frame.boarder_width+8), Frame.size[0]-Frame.boarder_width*2-16)
    frame = Frame(boxes)

    # test CSV loader
    for card in csv_loader.cards_from("CardDesigns.csv"):
        print(card)
        frame.render(card)            
        break
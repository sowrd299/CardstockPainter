import csv_loader
from frame import Frame
from text_box import TextBox
from PIL import Image


if __name__ == "__main__":
    print("Starting...")

    frame = Frame.open_from_xml("FrameData.xml")

    # test CSV loader
    for card in csv_loader.cards_from("CardDesigns.csv"):
        print(card) # testing
        rcard = frame.render(card)
        rcard.save("Output/"+card["Name"].replace(" ", "")+".png") 
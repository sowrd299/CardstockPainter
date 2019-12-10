import csv_loader
import tkinter
from frame import Frame

# TODO: make this all OOP

# refreshed what is currently being shown
def refresh():

    global photo
    global rcard

    # the card display
    # TODO: don't re-render if don't need to
    rcard = frame.render(card) 
    photo = rcard.get_tk_photoimage()
    card_disp.config(image = photo)

    # the next button
    next_actions = []
    if will_save.get():
        next_actions.append("save")
    next_button.config(text = "Next{0}".format(" (will {0})".format(",".join(next_actions)) if next_actions else ""))

# advances to the next card
def next_card():

    global card

    if will_save.get():
        rcard.save("Output/"+card["Name"].replace(" ","")+".png")

    card = next(cards)
    print("Card is now",card["Name"])
    refresh()


if __name__ == "__main__":
    print("Starting...")

    # setup basics
    frame = Frame.open_from_xml("/home/rnw/Dropbox/Games/Ashworld/AshworldCampaigns/FrameData.xml")
    root = tkinter.Tk()
    root.title("Card Renderer")
    cards =  csv_loader.cards_from("CardData.csv")

    # variables
    will_save = tkinter.IntVar(root)

    # setup gui
    card_disp = tkinter.Label(root)
    card_disp.pack()
    save_box = tkinter.Checkbutton(root, text="Save Card", variable=will_save, command=refresh)
    save_box.pack()
    next_button = tkinter.Button(root,text="Next", command=next_card)
    next_button.pack()

    # begin
    next_card()
    root.mainloop()
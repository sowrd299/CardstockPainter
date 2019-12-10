import csv_loader
import tkinter
from frame import Frame
from pdf_renderer import PdfRenderer

# TODO: make this all OOP

def render():

    global rcard
    global photo

    rcard = frame.render(card) 
    photo = rcard.get_tk_photoimage()

# refreshed what is currently being shown
def refresh():

    # the card display
    # TODO: don't re-render if don't need to
    if finished:
        card_disp.config(image = "", text = "\n\nNo more cards.\n\n")
    else:
        card_disp.config(image = photo)

    # the next button
    next_actions = []
    if will_save.get():
        next_actions.append("save")
    if will_pdf.get():
        next_actions.append("add to pdf")
    next_button.config(text = "Next{0}".format(" (will {0})".format(", ".join(next_actions)) if next_actions else ""))

def apply_actions():

    global pdf

    if not finished:

        if will_save.get():
            rcard.save("Output/"+card["Name"].replace(" ","")+".png")

        if will_pdf.get():
            if not pdf:
                pdf = PdfRenderer("./output.pdf")
            pdf.add(rcard.get_image())

# advances to the next card
def next_card():

    global card
    global finished

    apply_actions()

    if not finished:
        try:
            card = next(cards)
            print("Card is now",card["Name"])
            render()
        except StopIteration as e:
            finished = True

    refresh()


def save_and_exit():

    apply_actions()
    if pdf:
        pdf.save()
    root.quit()


if __name__ == "__main__":
    print("Starting...")

    # setup basics
    frame = Frame.open_from_xml("/home/rnw/Dropbox/Games/Ashworld/AshworldCampaigns/FrameData.xml")
    root = tkinter.Tk()
    root.title("Card Renderer")
    cards =  csv_loader.cards_from("CardData.csv")
    pdf = None
    finished = False # tracks if have made it to the end of the list of cards

    # variables
    will_save = tkinter.IntVar(root)
    will_pdf = tkinter.IntVar(root)

    # setup gui
    card_disp = tkinter.Label(root)
    card_disp.pack()

    checkboxes = tkinter.Frame(root)
    save_box = tkinter.Checkbutton(checkboxes, text="Save Image", variable=will_save, command=refresh)
    save_box.pack(side = tkinter.LEFT)
    pdf_box = tkinter.Checkbutton(checkboxes, text="Add to PDF", variable=will_pdf, command=refresh)
    pdf_box.pack(side = tkinter.LEFT)
    checkboxes.pack()

    buttons = tkinter.Frame(root)
    next_button = tkinter.Button(buttons,text="Next", command=next_card)
    next_button.pack(side = tkinter.LEFT)
    exit_button = tkinter.Button(buttons, text="Save&Exit", command=save_and_exit)
    exit_button.pack(side = tkinter.LEFT)
    buttons.pack()

    # begin
    next_card()
    root.mainloop()
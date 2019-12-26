import csv_loader
import tkinter
from frame import Frame
from pdf_renderer import PdfRenderer
from gui import RendererUI


if __name__ == "__main__":

	print("Starting...")

	# setup basics
	root = tkinter.Tk()
	root.title("Card Renderer")
	ui = RendererUI(Frame.open_from_xml, csv_loader.cards_from, root)

	root.mainloop()
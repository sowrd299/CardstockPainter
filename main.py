import csv_loader
import xml_loader
import tkinter
import sys
from pdf_renderer import PdfRenderer
from gui import RendererUI


if __name__ == "__main__":

	print("Starting...")

	# setup basics
	root = tkinter.Tk()
	root.title("Card Renderer")
	ui = RendererUI(xml_loader.frame_from, csv_loader.cards_from, root, initialdir=sys.argv[1])

	root.mainloop()
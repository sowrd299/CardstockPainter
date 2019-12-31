import tkinter
from tkinter import filedialog
from pdf_renderer import PdfRenderer

# a class for a UI element that opens files
class FileOpenerUI():

	not_loaded_text = "NO FILE LOADED"

	def __init__(self, name, root, on_load, file_class = open):

		self.name = name
		self.root = tkinter.Frame(root)
		self.on_load = on_load
		self.file_class = file_class

		# the UI itself
		self.name_label = tkinter.Label(self.root, text="{0}: ".format(name))
		self.name_label.pack(side = tkinter.LEFT)
		self.file_label = tkinter.Label(self.root, text=self.not_loaded_text)
		self.file_label.pack(side = tkinter.LEFT)
		self.button = tkinter.Button(self.root, text="Open", command=self.load)
		self.button.pack(side = tkinter.LEFT)

		# turn off hidden files
		try:
			# call a dummy dialog with an impossible option to initialize the file
			# dialog without really getting a dialog window; this will throw a
			# TclError, so we need a try...except :
			try:
				root.tk.call('tk_getOpenFile', '-foobarbaz')
			except TclError:
				pass
			# now set the magic variables accordingly
			root.tk.call('set', '::tk::dialog::file::showHiddenBtn', '1')
			root.tk.call('set', '::tk::dialog::file::showHiddenVar', '0')
		except:
			pass


	def pack(self, *args, **kwargs):
		self.root.pack(*args, **kwargs)

	def load(self):

		path = filedialog.askopenfilename(title="Open {0}".format(self.name))
		file = self.file_class(path)
		self.file_label.config(text = path)
		self.on_load(file)


class RendererUI():

	def __init__(self, frame_class, card_class, window):

		# basicis
		self.root = tkinter.Frame(window)
		self.frame = None
		self.cards = None

		# misc state variables
		self.pdf = None
		self.finished = False # tracks if have made it to the end of the list of cards
		self.rcard = None

		# variables
		self.will_save = tkinter.IntVar(self.root)
		self.will_pdf = tkinter.IntVar(self.root)

		# file loading
		self.frame_loader = FileOpenerUI("Frame Data", self.root, self.set_frame, frame_class)
		self.frame_loader.pack()
		self.card_loader = FileOpenerUI("Card Data", self.root, self.set_cards, card_class)
		self.card_loader.pack()

		# card disp gui
		self.card_disp = tkinter.Label(self.root)
		self.card_disp.pack()

		# action checkboxes
		self.checkboxes = tkinter.Frame(self.root)
		self.save_box = tkinter.Checkbutton(self.checkboxes, text="Save Image", variable=self.will_save, command=self.refresh)
		self.save_box.pack(side = tkinter.LEFT)
		self.pdf_box = tkinter.Checkbutton(self.checkboxes, text="Add to PDF", variable=self.will_pdf, command=self.refresh)
		self.pdf_box.pack(side = tkinter.LEFT)
		self.checkboxes.pack()

		# control buttons
		self.buttons = tkinter.Frame(self.root)
		self.next_button = tkinter.Button(self.buttons,text="Next", command=self.next_card)
		self.next_button.pack(side = tkinter.LEFT)
		self.exit_button = tkinter.Button(self.buttons, text="Save&Exit", command=self.save_and_exit)
		self.exit_button.pack(side = tkinter.LEFT)
		self.buttons.pack()

		# begin
		self.root.pack()

	def set_frame(self, frame):
		self.frame = frame
		if self.cards:
			self.next_card()

	def set_cards(self, cards):
		self.cards = cards
		if self.frame:
			self.next_card()

	def render(self):

		self.rcard = self.frame.render(self.card) 
		self.photo = self.rcard.get_tk_photoimage()

	# refreshed what is currently being shown
	def refresh(self):

		# the card display
		# TODO: don't re-render if don't need to
		if self.finished:
			self.card_disp.config(image = "", text = "\n\nNo more cards.\n\n")
		else:
			self.card_disp.config(image = self.photo)

		# the pdf check box (tracks curser)
		if self.pdf:
			self.pdf_box.config(text = "Add to Pdf\n(Page {0}, Row {2}, Column {1})".format(*self.pdf.get_next_position()))

		# the next button
		next_actions = []
		if self.will_save.get():
			next_actions.append("save")
		if self.will_pdf.get():
			next_actions.append("add to pdf")
		self.next_button.config(text = "Next{0}".format(" (will {0})".format(", ".join(next_actions)) if next_actions else ""))

	def apply_actions(self, rcard):

		if self.will_save.get():
			rcard.save(self.save_dir+card["Name"].replace(" ","")+".jpg")

		if self.will_pdf.get():
			if not self.pdf:
				self.pdf = PdfRenderer("./output.pdf")
			self.pdf.add(self.rcard.get_image())

	# advances to the next card
	def next_card(self):

		if not self.finished:

			self.apply_actions(self.rcard)

			try:
				self.card = next(self.cards)
				print("Card is now",self.card["Name"])
				self.render()
			except StopIteration as e:
				self.finished = True

		self.refresh()


	def save_and_exit(self):

		self.apply_actions(self.rcard)
		if self.pdf:
			self.pdf.save()
		self.root.quit()
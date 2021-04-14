'''
A file to export data compatible with Lackey CCG
https://lackeyccg.com/tutorialplugin.html
'''

import os

class CsvExporter():

    NAME = "Name"
    SET = "Set"
    IMAGE = "Image"

    val_delimiter = "\t"
    full_name = "'{Name}' + (', {Subtitle}' if '{Subtitle}' else '')"
    req_cols = [NAME, SET, IMAGE]
    req_cols_set = set(req_cols)

    def __init__(self, path):
        self.path = path
        self.cols = [] # the header for the columns of the card


    # returns the highest-level directory that contains the image but not the card data file
    # TODO: this is a stupid way to do this
    def get_set_from_img_path(self, img_path):
        prefix = os.path.commonpath([self.path, img_path])
        return os.path.dirname(img_path - prefix)


    # Sets up the known columns of the file to match the data from the given card
    def make_cols(self, card):
        self.cols = list(self.req_cols)
        for col in card.singleton_keys(): 
            if not col in self.req_cols_set:
                self.cols.append(col)


    # A generator
    def get_values(self, card, set_name="", img_name=""):
        val = ""
        for col in self.cols:
            if col == self.NAME:
                val = card.eval_card_field(self.full_name)
            elif col == self.SET:
                val = set_name
            elif col == self.IMAGE:
                val = img_name.split(".")[0] # NOTE: Removes the extension
            elif col in card:
                val = card[col]
            else:
                print('Failed to find key {} in CSV context, treating as empty...'.format(col))

            yield str(val)


    # Writes the given card into the file
    def add(self, card, **kwargs):
        if not self.cols:
            self.make_cols(card)
        row = self.val_delimiter.join(val for val in self.get_values(card, **kwargs))
        print(row) # TODO: Testing
'''
This manages importing the CSV data
It returns lines of the CSV as dicts
'''

# a generator,
# each itteration returns the next line represented as a dict
# TODO: deal with line splits... later
def cards_from(file : str, split_char : str = '\t'):
    with open(file) as f:
        names = f.readline().rstrip().split(split_char)
        for line in f.readlines():
            line = line.rstrip()
            vals = line.split(split_char)
            if any(vals):
                yield dict(zip(names, vals))

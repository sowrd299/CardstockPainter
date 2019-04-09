'''
This manages importing the CSV data
It returns lines of the CSV as dicts
'''

# a generator,
# each itteration returns the next line represented as a dict
def CardsFrom(file : str, split_char = ',' : str):
    with open(file) as f:
        names = f.readline().split(split_char)
        for line in f.readlines():
            yield dict(zip(names, line.split(split_char)))

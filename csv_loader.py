'''
This manages importing the CSV data
It returns lines of the CSV as dicts
'''

from tools import PrettyTuple, EMPTY

# replaces some uncommon unicode chars with ASCII equivilants
def filter_complex_chars(c : str):
	filters = dict()
	filters['\u201c'] = '"'
	filters['\u201d'] = '"'
	filters['\u2013'] = '-'
	filters['\u2014'] = '-'
	filters['\u2019'] = '\''
	if c in filters:
		return filters[c]
	return c


# processes and formats a single value that has been extracted from CSV
# Supports interpreting non-singleton values as tuples
def eval_value(val : str, tuple_char : str):
	if not val:
		return EMPTY
	elif tuple_char in val:
		return PrettyTuple(val.split(tuple_char))
	return val


# a generator,
# a version of readlines that respects CSV syntax more closely
def read_csv_lines(file : open, split_char : str, line_char : str, str_char : str, tuple_char : str):

	print("Reading with delimiters: '{}', '{}'....".format(split_char, str_char))
	
	in_str = False
	line = []
	current_value = ""
	c = file.read(1)

	while c:
		c = filter_complex_chars(c) 
		# handle diferent chars
		# split char
		if c == split_char and not in_str:
			line.append(eval_value(current_value, tuple_char))
			current_value = ""
		# end of line char
		elif c == line_char and not in_str:
			line.append(current_value)
			current_value = ""
			# end and yield the line
			yield line
			line = []
		# string begin/end char
		elif c == str_char:
			in_str = not in_str
		# content characters
		else:
			current_value += c

		c = file.read(1) 

# a generator,
# each itteration returns the next line represented as a dict
def cards_from(file : str, split_char : str = '\t', str_char : str = '"', tuple_char : str = ","):
	with open(file) as f:
		read = read_csv_lines(f, split_char, "\n", str_char, tuple_char)
		names = next(read)
		for vals in read:
			if any(vals):
				card = dict(zip(names, vals))

				# make tuple values accessible
				# handles cases where a single-value tuple may not appear as such
				extra_entries = dict()
				for k,v in card.items():
					t = v if isinstance(v, tuple) else (v,)
					for i,entry in enumerate(t):
						extra_entries["{}_{}".format(k,i)] = entry
				card.update(extra_entries)

				yield card
    
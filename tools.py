class DictTree():

	TERMINATOR = "FINNISHED" # marks the end of a string in the tree

	# Takes the dictionary this will represent
	def __init__(self, d : {str : object}):
		self.tree = dict()
		# add the starting values
		for k,v in d.items():
			self.set_entry(k,v)

	# adds the given value to the dictionary
	def set_entry(self, k : str, v : object):
		# explore down the tree, following the key
		branch = self.tree
		for i in k:
			# add branches as necessary
			if not i in branch:
				branch[i] = dict()
			branch = branch[i]
		# must used eos entry in case one key is a substring of another
		branch[self.TERMINATOR] = v

	# returns the first entry that is a left-justrified substring of the given
	#   key, as well as that substring key
	# returns None if not possible
	def get_first_entry(self, k : str):

		branch = self.tree 
		key_used = ""

		for i in k:

			key_used += i

			if self.TERMINATOR in branch:
				return (key_used, branch[self.TERMINATOR])

			if i not in branch.keys():
				return (k, None)
				
			branch = branch[i]

		if self.TERMINATOR in branch: # TODO: this probably doesn't need to be here... oh well
			return (key_used, branch[self.TERMINATOR])
		
		return (k, None)

if __name__ == "__main__":
	d = {"b" : 1, "aa": 2, "aac": 3, "ab" :4}
	dt = DictTree(d)
	print(dt.tree)
	e = dt.get_first_entry("aa")
	print(e)
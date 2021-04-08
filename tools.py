# a base class for classes that cannont be put into eval text in their current form
# These objects reject the norm that "repr" need to return legal python
# ...but conform after "make_eval_safe" has been called on them
class _EvalDangerous():
	def make_eval_safe(self):
		raise NotImplementedError


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


# An object that acts as the "defualt in all types"
#	...and is generally fail-safe
class _EmptyValue():
	def __bool__(self):
		return False
	def __getitem__(self, key):
		return self
	def __repr__(self):
		return 'EMPTY'
	def __hash__(self):
		return hash("")
	def __lt__(self, other):
		return 0 < other
	def __lte__(self, other):
		return 0 <= other
	def __eq__(self, other):
		if self is other:
			return True
		return 0==other
	def __ne__(self, other):
		return not self is other and 0!=other
	def __gt__(self, other):
		return 0 > other
	def __gte__(self, other):
		return 0 >= other
	def make_eval_safe(self):
		return _EvalSafeEmptyValue()

# this is the default to keep "EMPTY" out of English text
class _PrettyEmptyValue(_EmptyValue, _EvalDangerous):
	eval_safe = _EmptyValue()
	def __repr__(self):
		return ""
	def make_eval_safe(self):
		return self.eval_safe

# a signleton of type empty
EMPTY = _PrettyEmptyValue()


# A version of tuples that is fail-safe for illegal accesses
class DefaultTuple(tuple):
	_default = EMPTY
	def __getitem__(self, key):
		try:
			super().__getitem__(key)
		except IndexError:
			return self._default
	def __repr__(self):
		return "DefaultTuple({})".format(super().__repr__())


# a tuple that looks nice and clean when put in a string
class PrettyTuple(DefaultTuple):
	join_char = ","
	def __repr__(self):
		return self.join_char.join(self)
	def make_eval_safe(self):
		return DefaultTuple(self)

# returns if the given object is eval dangerous
def is_eval_dangerous(obj : object):
	try:
		eval(repr(obj))
		return True
	except Exception:
		return False

# attempts to convert objects into a form where __repr__ produces legal python
def make_eval_safe(obj : object):
	if isinstance(obj, _EvalDangerous):
		return obj.make_eval_safe()
	return obj


if __name__ == "__main__":
	d = {"b" : 1, "aa": 2, "aac": 3, "ab" :4}
	dt = DictTree(d)
	print(dt.tree)
	e = dt.get_first_entry("aa")
	print(e)
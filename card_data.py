from tools import PrettyTuple, EMPTY
import re

# part of XML handling
# a place for cashing regex expected to be seen often

class CardData(dict):

    tuple_char = ","
    known_regex = dict()
    index_char = "_"

    def __init__(self, *args, mapping = [], **kwargs):
        super().__init__(*args, **kwargs)
        for k,v in mapping:
            self[k] = v

    def _super_set(self, k, v):
        super().__setitem__(k, v)

    # processes and formats a single value that has been extracted from CSV
    # Supports interpreting non-singleton values as tuples
    # handles cases where a single-value tuple may not appear as such
    def eval_value(self, val : str):
        if not val:
            return EMPTY
        return PrettyTuple(val.split(self.tuple_char))

    # make tuple values accessible
    def index_tuple_value(self, k, v):
        t = v if isinstance(v, tuple) else (v,)
        for i,entry in enumerate(t):
            self._super_set("{}{}{}".format(k,self.index_char,i), entry)

    def __getitem__(self, key):
        return super().__getitem__(key)

    def __setitem__(self, key, val):
        v = self.eval_value(val)
        self._super_set(key, v)
        self.index_tuple_value(key, v)

    # generator
    def singleton_items(self):
        for k,v in self.items():
            unindexed = self.index_char.join(k.split(self.index_char)[:-1])
            if not (unindexed and unindexed in self):
                yield k,v

    # generator
    def singleton_keys(self):
        for k,_ in self.singleton_items():
            yield k

    # evaluates a parameterized field of a card
    # TODO: This *might* want to be its own thing? or at least the part getting stuff from dicts
    def eval_card_field(self, field_value : str, **args ):

        card = self

        # HERE ARE THE FUNCTIONS  CALLABLE FROM CARD FIELDS

        def indexes_of(matches):
            if matches:
                return [(match.start(), match.end()) for match in matches]
            else:
                return None

        def regex_matches(regex, text):
            compiled_regex = None
            if regex in self.known_regex:
                compiled_regex = self.known_regex[regex]
            else:
                compiled_regex = re.compile(regex)
                self.known_regex[regex] = compiled_regex
            matches = []
            pos = 0
            while True:
                match = compiled_regex.search(text, pos)
                if match:
                    matches.append(match)
                    pos = match.end()
                else:
                    return matches

        def make_alnum(text):
            return "".join( filter(lambda  c : c.isalnum(), text) )

        All = (0,-1)
            
        # Assemble the context, evaluate and return

        context = card
        if args:
            context = dict(card, **args)

        r = ""
        try:
            r = eval(field_value.replace("'","'''").format(**context))
        # Errors in {Var}'s being used
        except KeyError as e:
            print('Failed to find key "{}" in context, treating as empty...'.format(e))
            self[eval(str(e))] = EMPTY # NOTE: This is a weird trick for finding the failed key...
            return self.eval_card_field(field_value, **args)
        # Errors in python syntax there-after
        except (SyntaxError, TypeError, NameError) as e:
            
            # Handle correcting for eval-dangerous without a fuss
            if any(map(is_eval_dangerous, context.values())): 
                return eval_card_field(field_value, { k:make_eval_safe(v) for k,v in context.items() })

            print('Illegal syntax in field "{}", evalling as "{}"!'.format(field_value, field_value.replace("'","'''").format(**context)))

        return r
from spacy.matcher import DependencyMatcher
from spacy.language import Language


pattern1 = [
    {"RIGHT_ID": "found_nsubj", "RIGHT_ATTRS": {"DEP": "nsubj"}},
    {
        "LEFT_ID": "found_nsubj",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "ADJ", "NOUN"]}},
    },
]

pattern2 = [
    {"RIGHT_ID": "found_nsubj", "RIGHT_ATTRS": {"DEP": "nsubj"}},
    {
        "LEFT_ID": "found_nsubj",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "ADJ", "NOUN"]}},
    },
    {
        "LEFT_ID": "found_verb",
        "REL_OP": ">",
        "RIGHT_ID": "found_obj",
        "RIGHT_ATTRS": {"DEP": "obj"},
    },
]

pattern3 = [
    {"RIGHT_ID": "found_noum", "RIGHT_ATTRS": {"POS": "NOUN"}},
    {
        "LEFT_ID": "found_noum",
        "REL_OP": ">",
        "RIGHT_ID": "found_amod",
        "RIGHT_ATTRS": {"DEP": "amod", "POS": "ADJ"},
        # "RIGHT_ATTRS": {"IN": [{"DEP": "amod"}, {"POS": "ADJ"}]},
    },
]

pattern4 = [
    {"RIGHT_ID": "found_nsubj", "RIGHT_ATTRS": {"DEP": "nsubj"}},
    {
        "LEFT_ID": "found_nsubj",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "ADJ", "NOUN"]}},
    },
    {
        "LEFT_ID": "found_verb",
        "REL_OP": ">",
        "RIGHT_ID": "found_advcl",
        "RIGHT_ATTRS": {"DEP": "advcl"},
    },
]

pattern5 = [
    {"RIGHT_ID": "found_conj", "RIGHT_ATTRS": {"DEP": "conj", "POS": "NOUN"}},
    {
        "LEFT_ID": "found_conj",
        "REL_OP": "<",
        "RIGHT_ID": "found_nsubj",
        "RIGHT_ATTRS": {"DEP": "nsubj"},
    },
    {
        "LEFT_ID": "found_nsubj",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "ADJ", "NOUN"]}},
    },
]

pattern6 = [
    {"RIGHT_ID": "found_nsubj", "RIGHT_ATTRS": {"DEP": "nsubj"}},
    {
        "LEFT_ID": "found_nsubj",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": {"IN": ["VERB", "ADJ", "NOUN"]}},
    },
    {
        "LEFT_ID": "found_verb",
        "REL_OP": ">",
        "RIGHT_ID": "found_comod",
        "RIGHT_ATTRS": {"DEP": "comod"},
    }
    
]


@Language.factory("pending_aspects_opinions_pipe")
def pending_aspects_opinions_pipe(nlp, name):
    return PendingAspectsOpinionsPipe(nlp)


class PendingAspectsOpinionsPipe:
    def __init__(self, nlp):
        self.matcher = DependencyMatcher(nlp.vocab)
        # self.matcher.add("found_nsubj", [nsubj_and_noun_verb_pat])
        self.matcher.add("found_nsubj", [pattern1, pattern2, pattern3, pattern4, pattern5, pattern6])
        # self.matcher.add("found_nsubj", [pattern5])

    def __call__(self, doc):
        try:
            matches = self.matcher(doc)
        except:
            raise ValueError(f"Error in matching '{doc.text}', INFO: {[(token, token.pos_, token.tag_, token.dep_, token.head) for token in doc]}")
        ic(matches)
        doc._.pending_aspects_opinions_i = [
            (matchidx[0], matchidx[-1]) for _, matchidx in matches
        ]
        doc._.pending_aspects_opinions_text = [
            (doc[asp].text.replace(" ", ""), doc[opi].text.replace(" ", ""))
            for asp, opi in doc._.pending_aspects_opinions_i
        ]
        return doc

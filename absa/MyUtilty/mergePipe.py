from spacy.language import Language
from spacy.matcher import DependencyMatcher
from spacy.util import filter_spans

compound_nn_pattern = [
    {"RIGHT_ID": "found_compound", "RIGHT_ATTRS": {"DEP": "compound:nn"}},
    {
        "LEFT_ID": "found_compound",
        "REL_OP": "<",
        "RIGHT_ID": "found_noun",
        "RIGHT_ATTRS": {"POS": "NOUN"},
    },
]

genitive_de_pattern = [
    {
        "RIGHT_ID": "found_nmod",
        "RIGHT_ATTRS": {"DEP": {"IN": ["nmod:assmod", "nmod:poss"]}},
    },
    {
        "LEFT_ID": "found_nmod",
        "REL_OP": "<",
        "RIGHT_ID": "found_noun",
        "RIGHT_ATTRS": {"POS": "NOUN"},
    },
]

ccomp_pattern = [
    {"RIGHT_ID": "found_ccomp", "RIGHT_ATTRS": {"DEP": "ccomp"}},
    {
        "LEFT_ID": "found_ccomp",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": "VERB"},
    },
]

# a_n_mod_pattern = [
#     {"RIGHT_ID": "found_a_n_mod", "RIGHT_ATTRS": {"DEP": {"IN": ["amod", "nmod"]}}},
#     {
#         "LEFT_ID": "found_a_n_mod",
#         "REL_OP": "<",
#         "RIGHT_ID": "found_noun",
#         "RIGHT_ATTRS": {"POS": "NOUN"},
#     },
# ]

nmod_pattern = [
    {"RIGHT_ID": "found_nmod", "RIGHT_ATTRS": {"DEP": "nmod"}},
    {
        "LEFT_ID": "found_nmod",
        "REL_OP": "<",
        "RIGHT_ID": "found_noun",
        "RIGHT_ATTRS": {"POS": "NOUN"},
    },
]

case_pattern = [
    {"RIGHT_ID": "found_case", "RIGHT_ATTRS": {"DEP": "case"}},
    {
        "LEFT_ID": "found_case",
        "REL_OP": "<",
        "RIGHT_ID": "found_noun",
        "RIGHT_ATTRS": {"POS": "NOUN"},
    },
]

advmod_predicate_adj_pattern = [
    {"RIGHT_ID": "found_advmod", "RIGHT_ATTRS": {"DEP": "advmod"}},
    {
        "LEFT_ID": "found_advmod",
        "REL_OP": "<",
        "RIGHT_ID": "found_adj",
        "RIGHT_ATTRS": {"POS": "ADJ"},
    },
]

neg_pattern = [
    {"RIGHT_ID": "found_neg", "RIGHT_ATTRS": {"DEP": "neg"}},
    {
        "LEFT_ID": "found_neg",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": "VERB"},
    },
]

obj_pattern = [
    {"RIGHT_ID": "found_obj", "RIGHT_ATTRS": {"DEP": "obj"}},
    {
        "LEFT_ID": "found_obj",
        "REL_OP": "<",
        "RIGHT_ID": "found_verb",
        "RIGHT_ATTRS": {"POS": "VERB"},
    },
]


@Language.factory("merge_pipe")
def merge_pipe(nlp, name):
    return MergePipe(nlp)


class MergePipe:
    def __init__(self, nlp):
        self.matcher = DependencyMatcher(nlp.vocab)
        self.matcher.add(
            "merge_patset",
            [
                compound_nn_pattern,
                genitive_de_pattern,
                ccomp_pattern,
                nmod_pattern,
                case_pattern,
                advmod_predicate_adj_pattern,
                neg_pattern,
                obj_pattern,
            ],
        )

    def __call__(self, doc):
        matches = self.matcher(doc)
      #   print("matches", matches)
        spans = [doc[min(l, r) : max(l, r) + 1] for _, [l, r] in matches]
        spans = filter_spans(spans)
        with doc.retokenize() as retokenizer:
            for span in spans:
                retokenizer.merge(span)
        return doc

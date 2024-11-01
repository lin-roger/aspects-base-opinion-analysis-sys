from spacy.pipeline import AttributeRuler
from spacy.language import Language

patterns = [
    {"patterns": [[{"TAG": "FW"}]], "attrs": {"POS": "X"}},
    {"patterns": [[{"TAG": "A"}]], "attrs": {"POS": "ADJ"}},
    {"patterns": [[{"TAG": "Caa"}]], "attrs": {"POS": "CCONJ"}},
    {"patterns": [[{"TAG": "Cab"}]], "attrs": {"POS": "X"}},
    {"patterns": [[{"TAG": {"IN": ["Cba", "Cbb"]}}]], "attrs": {"POS": "SCONJ"}},
    {
        "patterns": [[{"TAG": {"IN": ["D", "Da", "Dfa", "Dfb", "Dk"]}}]],
        "attrs": {"POS": "ADV"},
    },
    {"patterns": [[{"TAG": {"IN": ["Di", "SHI"]}}]], "attrs": {"POS": "AUX"}},
    {
        "patterns": [[{"TAG": {"IN": ["DM", "Na", "Nc", "Ncd", "Nd", "Nf", "Nv"]}}]],
        "attrs": {"POS": "NOUN"},
    },
    {"patterns": [[{"TAG": "I"}]], "attrs": {"POS": "INTJ"}},
    {"patterns": [[{"TAG": "Nb"}]], "attrs": {"POS": "PROPN"}},
    {"patterns": [[{"TAG": {"IN": ["Nes", "Nep"]}}]], "attrs": {"POS": "DET"}},
    {"patterns": [[{"TAG": {"IN": ["Neqa", "Neqb", "Neu"]}}]], "attrs": {"POS": "NUM"}},
    {"patterns": [[{"TAG": {"IN": ["Ng", "P"]}}]], "attrs": {"POS": "ADP"}},
    {"patterns": [[{"TAG": {"IN": ["Nh"]}}]], "attrs": {"POS": "PRON"}},
    {"patterns": [[{"TAG": {"IN": ["T", "DE"]}}]], "attrs": {"POS": "PART"}},
    {
        "patterns": [
            [
                {
                    "TAG": {
                        "IN": [
                            "COLONCATEGORY",
                            "COMMACATEGORY",
                            "DASHCATEGORY",
                            "DOTCATEGORY",
                            "ETCCATEGORY",
                            "EXCLAMATIONCATEGORY",
                            "PARENTHESISCATEGORY",
                            "PAUSECATEGORY",
                            "PERIODCATEGORY",
                            "QUESTIONCATEGORY",
                            "SEMICOLONCATEGORY",
                            "SPCHANGECATEGORY",
                            "WHITESPACE",
                        ]
                    }
                }
            ]
        ],
        "attrs": {"POS": "PUNCT"},
    },
    {
        "patterns": [
            [
                {
                    "TAG": {
                        "IN": [
                            "VA",
                            "VAC",
                            "VB",
                            "VC",
                            "VCL",
                            "VD",
                            "VE",
                            "VF",
                            "VG",
                            "VH",
                            "VHC",
                            "VI",
                            "VJ",
                            "VK",
                            "VL",
                            "V_2",
                            "VAC",
                            "VB",
                            "VC",
                            "VCL",
                            "VD",
                            "VE",
                            "VF",
                            "VG",
                            "VH",
                            "VHC",
                            "VI",
                            "VJ",
                            "VK",
                            "VL",
                            "V_2",
                        ]
                    }
                }
            ]
        ],
        "attrs": {"POS": "VERB"},
    },
]


@Language.factory("tag2pos")
def tag2posFactory(nlp: Language, name: str):
    tag2pos = AttributeRuler(nlp.vocab)
    tag2pos.add_patterns(patterns)
    return tag2pos

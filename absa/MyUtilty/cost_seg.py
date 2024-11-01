import hanlp
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from spacy.tokens import Doc

# TODO: OOM dep_text
class CostSegmenter:
    def __init__(self, vocab):
        self.vocab = vocab
        self.ws = CkipWordSegmenter(device=0)
        self.pos = CkipPosTagger(device=0)
        # self.dep = hanlp.load(hanlp.pretrained.dep.CTB9_UDC_ELECTRA_SMALL)
        self.dep = hanlp.load(hanlp.pretrained.dep.CTB9_DEP_ELECTRA_SMALL)

    def __call__(self, text):
        try:
            seg_text = self.ws([text], show_progress=False)
            pos_text = self.pos(seg_text, show_progress=False)
            dep_text = self.dep(seg_text, conll=False)
        except:
            raise ValueError(f"Error in segmenting '{text}'")
        post_dep_text = list(
            map(
                lambda x: [
                    (head - 1 if head != 0 else idx, dep_)
                    for idx, (head, dep_) in enumerate(x)
                ],
                dep_text,
            )
        )
        docList = [
            Doc(
                vocab=self.vocab,
                words=i[0],
                spaces=[False] * len(i[0]),
                tags=i[1],
                heads=list(zip(*i[2]))[0],
                deps=list(zip(*i[2]))[1],
            )
            for i in zip(seg_text, pos_text, post_dep_text)
        ]
        return docList[0]

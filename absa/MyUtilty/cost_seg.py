import hanlp
import sys
from ckip_transformers.nlp import CkipWordSegmenter, CkipPosTagger
from spacy.tokens import Doc

sys.setrecursionlimit(10000)

class CostSegmenter:
    def __init__(self, vocab):
        self.vocab = vocab
        self.ws = CkipWordSegmenter(device=0)
        self.pos = CkipPosTagger(device=0)
        # self.dep = hanlp.load(hanlp.pretrained.dep.CTB9_UDC_ELECTRA_SMALL)
        self.dep = hanlp.load(hanlp.pretrained.dep.CTB9_DEP_ELECTRA_SMALL)

    def __call__(self, text, max_len = 512):
        try:
            seg_text = self.ws([text], show_progress=False)
            while len(seg_text[-1]) > max_len:
                tmp = seg_text[-1]
                seg_text[-1] = tmp[:max_len]
                seg_text.append(tmp[max_len:])
            pos_text = self.pos(seg_text, show_progress=False)
            dep_text = self.dep(seg_text, conll=False)
        except Exception as e:
            raise ValueError(f"Error in segmenting '{text}', {e}")
        post_dep_text = list(
            map(
                lambda x: [
                    ((head - 1 if head != 0 else idx), dep_)
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
        return Doc.from_docs(docList)
        # return docList[0]

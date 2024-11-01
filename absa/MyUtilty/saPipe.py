from spacy.language import Language
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    AutoModelForSequenceClassification,
    BertTokenizerFast,
    pipeline,
)
from scipy.cluster.hierarchy import linkage, dendrogram, to_tree
from types import MethodType
import torch
import numpy as np



@Language.factory("pending_aspects_opinions_pipe")
def pending_aspects_opinions_pipe(nlp, name):
    return PendingAspectsOpinionsPipe()


class PendingAspectsOpinionsPipe:
    def __init__(self, nlp):
        self.ckip_tokenizer = AutoTokenizer.from_pretrained("ckiplab/bert-base-chinese-ws")
        self.ckip_model = AutoModelForTokenClassification.from_pretrained("ckiplab/bert-base-chinese-ws").to("cuda")
        self.tokenizer = BertTokenizerFast.from_pretrained("ckiplab/bert-base-chinese")
        self.model = AutoModelForSequenceClassification.from_pretrained(
            "/workspaces/ABSA/checkpoint-2400",
            id2label={0: "negative", 1: "positive"},
            label2id={"negative": 0, "positive": 1},
        ).to("cuda")
        self.pip = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer, device=0, return_all_scores=True)
        self.explainer = self.shap.Explainer(self.pip, algorithm="partition")
        self.explainer.masker.clustering = MethodType(self.custom_clustering, self.explainer.masker)

    def __call__(self, doc):
        matches = self.matcher(doc)
        doc._.pending_aspects_opinions_i = [(asp, opi) for _, [asp, opi] in matches]
        doc._.pending_aspects_opinions_text = [
            (doc[asp].text.replace(" ", ""), doc[opi].text.replace(" ", ""))
            for asp, opi in doc._.pending_aspects_opinions_i
        ]
        # print([(asp, opi) for _, [asp, opi] in matches])
        return doc
    
    def custom_clustering(self, inst, s):
        tokens = inst._segments_s
        tok  = self.ckip_tokenizer(s, return_tensors="pt").to("cuda")
        with torch.no_grad():
            logits = self.ckip_model(**tok).logits
            logits = torch.softmax(logits, dim=-2)[:, :, 0][0].cpu().numpy()
        logits[0], logits[-1] = 1, 1

        inX = np.arange(len(tokens)).reshape(-1, 1)
        f = lambda x, y: logits[int(min(x, y))+1:int(max(x, y))+1].sum()
        Z = linkage(inX, metric=f)
        return Z

import shap
from transformers import (
    AutoModelForSequenceClassification,
    BertTokenizerFast,
    pipeline,
)
from types import MethodType
from scipy.cluster.hierarchy import linkage
from functools import partial
from icecream import ic
import numpy as np


class ShapInfer:
    def __init__(self):
        tokenizer = BertTokenizerFast.from_pretrained("ckiplab/bert-base-chinese", return_tensors="pt")
        model = AutoModelForSequenceClassification.from_pretrained(
            "/workspaces/ABSA/checkpoint-2400"
        ).to("cuda")
        pip = pipeline(
            "sentiment-analysis",
            model=model,
            tokenizer=tokenizer,
            device=0,
            return_all_scores=True,
        )
        self.explainer = shap.Explainer(pip, algorithm="partition")

    def __call__(self, doc):
        def custom_clustering(inst, s):
            tokens = inst._segments_s
            inX = np.arange(len(tokens)).reshape(-1, 1)
            f = lambda x, y: doc._.dist[int(min(x, y)) + 1 : int(max(x, y)) + 1].sum()
            Z = linkage(inX, metric=f)
            return Z

        self.explainer.masker.clustering = MethodType(
            custom_clustering, self.explainer.masker
        )
        shap_values = self.explainer([doc.text])
        maxshap = self._shapValueAlignToken(shap_values.values, doc)
        for i, pair in enumerate(doc._.pending_aspects_opinions_i):
            asp, opi = pair
            if abs(doc[opi]._.n_value / maxshap) < 0.1:
                p = "NAT"
            else:
                p = "NEG" if doc[opi]._.n_value > 0 else "POS"

            doc._.aspect_sentiment_triplets.append(
                (
                    doc[asp].text.replace(" ", ""),
                    doc[opi].text.replace(" ", ""),
                    p,
                )
            )
        return doc

    def _shapValueAlignToken(self, sv, doc):
        svn = sv[0, 1:-1, 0]
        i = 0
        for tok in doc:
            ctok = tok.text.replace(" ", "")
            n_value = svn[i : i + len(ctok)].sum()
            i += len(ctok)
            tok._.n_value = n_value
        return max(abs(svn.min()), abs(svn.max()))

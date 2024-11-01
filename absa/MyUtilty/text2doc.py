from typing import Any
from transformers import AutoTokenizer, AutoModelForTokenClassification
from nlp2 import clean_all

import spacy
import spacy.tokens
import torch
import numpy as np

from ckip_transformers.nlp.util import CkipTokenClassification
from ckip_transformers.nlp import CkipWordSegmenter

class Text2Doc:
    def __init__(self, nlp: spacy.language.Language):
        self.pipe = nlp
        self.ws = CkipWordSegmenter(device=0)

    def __call__(self, raw_texts: list[str]) -> list[spacy.tokens.Doc]:
        texts = [clean_all(i) for i in raw_texts]
        texts = [" ".join(words) for words in self.ws(texts)]
        return list(self.pipe.pipe(texts))


# class Text2Doc:
#     def __init__(self, nlp: spacy.language.Language):
#         self.pipe = nlp
#         self.ckip_tokenizer = AutoTokenizer.from_pretrained(
#             "ckiplab/bert-base-chinese-ws"
#         )
#         self.ckip_model = AutoModelForTokenClassification.from_pretrained(
#             "ckiplab/bert-base-chinese-ws"
#         ).to("cuda")

#     def __call__(self, raw_texts: list[str]) -> list[spacy.tokens.Doc]:
#         texts = [self._preprocess(i) for i in raw_texts]
#         textDistLabels = [(i, self._inferDistAndLable(i)) for i in texts]
#         wordsDistLabels = [
#             (self._textSegByLabel(text, label), dist)
#             for text, (dist, label) in textDistLabels
#         ]
#         return map(self._wordsDistLabels2doc, wordsDistLabels)

#     def _preprocess(self, text: str) -> str:
#         text = clean_all(text)
#         text = self.ckip_tokenizer.decode(
#             self.ckip_tokenizer.encode(text, truncation=True, add_special_tokens=False)
#         )
#         return text.replace(" ", "")

#     def _wordsDistLabels2doc(
#         self, wordsDist: tuple[list[str], np.ndarray]
#     ) -> spacy.tokens.Doc:
#         doc = self.pipe(" ".join(wordsDist[0]))
#         doc._.dist = wordsDist[1]
#         return doc

#     def _inferDistAndLable(self, text: str) -> tuple[np.ndarray, list[int]]:
#         tok = self.ckip_tokenizer([text], truncation=True, return_tensors="pt").to(
#             "cuda"
#         )
#         with torch.no_grad():
#             logits = self.ckip_model(**tok).logits
#             segLable = torch.argmax(logits, dim=-1)[0][1:].cpu().tolist()
#             dist = torch.softmax(logits, dim=-2)[:, :, 0][0].cpu().numpy()
#         dist[0], dist[-1] = 1, 1
#         return (dist, segLable)

#     def _textSegByLabel(self, text: str, segLable: list[int]) -> list[str]:
#         words = []
#         for lable, word in zip(segLable, text):
#             if lable == 0:
#                 words.append(word)
#             else:
#                 words[-1] += word
#         return words


# class CustCkipWordSeg(CkipTokenClassification):
#     _model_names = {
#         "albert-tiny": "ckiplab/albert-tiny-chinese-ws",
#         "albert-base": "ckiplab/albert-base-chinese-ws",
#         "bert-tiny": "ckiplab/bert-tiny-chinese-ws",
#         "bert-base": "ckiplab/bert-base-chinese-ws",
#     }

#     def __init__(
#         self,
#         model: str = "bert-base",
#         **kwargs,
#     ):
#         model_name = kwargs.pop("model_name", self._get_model_name(model))
#         super().__init__(model_name=model_name, **kwargs)

#     def __call__(
#         self,
#         input_text: list[str],
#         *,
#         use_delim: bool = False,
#         **kwargs,
#     ) -> list[list[str]]:

#         (
#             logits,
#             index_map,
#         ) = super().__call__(input_text, use_delim=use_delim, **kwargs)

#         output_text = []
#         for sent_data in zip(input_text, index_map):
#             output_sent = []
#             word = ""
#             for input_char, logits_index in zip(*sent_data):
#                 if logits_index is None:
#                     if word:
#                         output_sent.append(word)
#                     output_sent.append(input_char)
#                     word = ""
#                 else:
#                     logits_b, logits_i = logits[logits_index]

#                     if logits_b > logits_i:
#                         if word:
#                             output_sent.append(word)
#                         word = input_char
#                     else:
#                         word += input_char

#             if word:
#                 output_sent.append(word)
#             output_text.append(output_sent)

#         return output_text, logits, index_map

import numpy as np
import pandas as pd
import scann
import re
from icecream import ic
from nlp2 import split_text_in_all_comb
from scipy.special import softmax
from ckip_transformers.nlp import CkipWordSegmenter


class EmoBankSearch:
    def __init__(self, nlp):
        # self.polarity_dict = {
        #     0: "NEG",
        #     1: "POS",
        #     2: "NAT",
        # }
        self.polarity_dict = {
            0: "負面",
            1: "正面",
            2: "中性",
        }
        self.vecs = nlp.vocab.vectors
        self.bank = np.load("./bank.npy", allow_pickle=True)
        self.embedding = np.vstack(self.bank[:, 1])
        self.scann = (
            scann.scann_ops_pybind.builder(self.embedding, 10, "dot_product")
            .score_brute_force()
            .build()
        )
        self.ws_driver = CkipWordSegmenter(model="bert-base", device=0)
        self.pat = r"[！？｡。＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏.]"

    def __call__(self, doc, to_dict=False, to_polarity=False):
        doc._.aspect_sentiment_triplets = [
            (a, o, self._get_valence(o))
            for a, o in doc._.pending_aspects_opinions_text
        ]
        if to_dict:
            doc._.aspect_sentiment_triplets = [
                {"a": i[0], "o": i[1], "p": i[2]}
                for i in doc._.aspect_sentiment_triplets
            ]
        if to_polarity:
            doc._.aspect_sentiment_triplets = [
                {"a": i[0], "o": i[1], "p": self._valence_to_polarity(i[2])}
                for i in doc._.aspect_sentiment_triplets
            ]
        return doc

    def _valence_to_polarity(self, valence, delta=0.5):
        if valence > 5 + delta:
            return self.polarity_dict[1]
        elif valence < 5 - delta:
            return self.polarity_dict[0]
        else:
            return self.polarity_dict[2]

    def _get_valence(self, word, alg="avg"):
        """
        Calculate the polarity of a word based on its search results.

        Parameters:
        - word (str): The word to calculate polarity for.
        - delta (float): The threshold value to determine positive or negative polarity. Default is 0.5.
        - alg (str): The algorithm to use for polarity calculation. Options are "avg" (default) and "softmax".

        Returns:
        - str: The polarity of the word. Possible values are "POS" (positive), "NEG" (negative), or "NAT" (neutral).
        """
        try:
            word = re.sub(self.pat, "", word)
            tmp = self.search(word, n=5)

            if tmp[2][0] > 0.95:
                pv = tmp[1][0]
            elif alg == "avg":
                pv = tmp[1].mean()
            elif alg == "softmax":
                pv = np.sum(softmax(tmp[2]) * tmp[1])
            else:
                raise ValueError(f"Invalid algorithm: {alg}")
            return pv
        except:
            print(f"word: {word} not found")
            return 5

    def search(self, word, n=1):
        try:
            vec = self._get_possible_vector(word)
            neighbors, distances = self.scann.search(vec, final_num_neighbors=n)
            q_words = self.bank[neighbors][:, 0]
            q_polarity = self.bank[neighbors][:, 2]
            # ic(q_words, q_polarity, distances)
            return (q_words, q_polarity, distances)
        except:
            assert False, f"word: {word} not found"

    def _get_word_vector(self, word, norm=True, enum=False):
        words = word.split()
        vec = np.zeros(self.vecs.shape[-1])

        for w in words:
            try:
                vec += self.vecs[w]
            except:
                if enum:
                    ic(w)
                    vec += self._get_word_vector(" ".join([*w]), norm=False)
                else:
                    return None

        if norm:
            vec = vec / np.linalg.norm(vec)
        return vec

    def _get_possible_vector(self, word):
        assert type(word) == str
        try:
            if len(word) <= 10:
                n_gram = split_text_in_all_comb(word)[::-1]
                for i in n_gram:
                    vec = self._get_word_vector(i)
                    if vec is not None:
                        ic(i)
                        # assert np.linalg.norm(vec) == 1.0, f"norm: {np.linalg.norm(vec)}"
                        return vec
                assert False, f"word: {word} not found"
            else:
                seg_word = " ".join(self.ws_driver([word], show_progress=0)[0])
                vec = self._get_word_vector(seg_word, enum=True)
                assert vec is not None, f"word: `{seg_word}` not found"
                return vec
        except:
            return None

import re
from itertools import product
from collections import Counter


class PatternDiscoverEngine:
    def __init__(self):
        self.pat_set = Counter()
        self.gost_AO = []
        
    def pat_serach(self, doc, t_pair_set):
        t_spans = []
        for a, o in t_pair_set:
            a_spans = self._findall(doc.text, a)
            o_spans = self._findall(doc.text, o)
            tmp = list(product(a_spans, o_spans))
            if tmp == []:
                # self.gost_AO.append((a, o))
                continue
            d_list = list(map(self._w_dist, *zip(*tmp)))
            idx = d_list.index(min(d_list))
            # print(d_list[idx], tmp[idx])
            t_spans.append(
                (
                    doc.char_span(tmp[idx][0][0], tmp[idx][0][1], alignment_mode="expand"),
                    doc.char_span(tmp[idx][1][0], tmp[idx][1][1], alignment_mode="expand"),
                )
            )
        # print(t_spans)
        any(map(self._pat_extract_by_span, t_spans))
        # return t_spans
    
    def _pat_extract_by_span(self, ao_span_tuple):
        a_span, o_span = ao_span_tuple
        dep = None
        if a_span.root.head in o_span:
            dep = a_span.root.dep_
            self.pat_set.update([f"{dep}, {a_span.root.pos_}, {o_span.root.pos_}, O_HEAD"])
        elif o_span.root.head in a_span:
            dep = o_span.root.dep_
            self.pat_set.update([f"{dep}, {a_span.root.pos_}, {o_span.root.pos_}, A_HEAD"])
    
    def _findall(self, text, q_str):
        role = re.compile(q_str, flags=re.I)
        return [i.span() for i in role.finditer(text)]
    
    def _w_dist(self, span1, span2):
        return min(abs(span1[0] - span2[1]), abs(span1[1] - span2[0]))

    def get_patterns(self):
        return self.pat_set
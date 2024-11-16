# %%
from nltk.util import everygrams
from nltk.lm import NgramCounter
from elasticsearch import Elasticsearch, helpers
import yaml
import pickle

with open("../config.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

allow_pos = set(config["allow_pos"])

# %%
es = Elasticsearch(
    "http://host.docker.internal:9200",
    verify_certs=False,
    basic_auth=("elastic", "123456"),
)

# %%
data_set = helpers.scan(
    es,
    index="docs",
    query={
        "_source": ["title_token", "title_tag", "context_token", "context_tag"],
        "query": {"match_all": {}},
    },
)

# %%
def tag_filter_by_pos(tag_list, pos_list, delim_set = "，,。：:；;！!？?"):
    if not tag_list:
        return []
    cleaned_tag_list = [[]]
    for tag, pos in zip(tag_list, pos_list):
        if tag in delim_set:
            cleaned_tag_list.append([])
        elif pos in allow_pos:
            cleaned_tag_list[-1].append(tag)
    return cleaned_tag_list

# %%
c = NgramCounter()

# %%
for doc in data_set:
    title_token = doc["_source"]["title_token"]
    title_tag = doc["_source"]["title_tag"]
    context_token = doc["_source"]["context_token"]
    context_tag = doc["_source"]["context_tag"]

    title_token = tag_filter_by_pos(title_token, title_tag)
    context_token = tag_filter_by_pos(context_token, context_tag)

    token_list = title_token + context_token
    gram_list = [list(everygrams(tokens, max_len=5)) for tokens in token_list]
    c.update(gram_list)
# %%
with open('../model_persistent/n_gram_model/n_gram.pickle','wb') as f:
    pickle.dump(c,f)
# %%

with open('../model_persistent/n_gram_model/n_gram.pickle','rb') as f:
    c_pic = pickle.load(f)
# %%

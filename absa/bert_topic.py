# %%
from calendar import c
from elasticsearch import Elasticsearch, helpers
from glom import glom
from umap import UMAP
from sklearn.feature_extraction.text import CountVectorizer
from bertopic import BERTopic
# from cuml.cluster import HDBSCAN
# from cuml.manifold import UMAP


import yaml
import numpy as np
import pandas as pd

# %%
with open("/workdir/config.yaml") as f:
    config = yaml.safe_load(f)

allow_pos = set(config["allow_pos"])
idx_name = config["index"]
body = {
    "_source": ["context_token", "context_tag", "context_vector"],
    "query": {"match_all": {}},
}

# %%
client = Elasticsearch(
    "http://elasticsearch:9200", verify_certs=False, basic_auth=("elastic", "123456")
)
res = list(
    helpers.scan(
        client,
        query=body,
        index=idx_name,
    )
)
vec_df = pd.DataFrame.from_dict(glom(res, "*._source"))

# %%
def tag_filter_by_pos(tag_list, pos_list):
    if not tag_list:
        return ""
    cleaned_tag_list = [tag for tag, pos in zip(tag_list, pos_list) if pos in allow_pos]
    return " ".join(cleaned_tag_list)


vec_df = vec_df[vec_df["context_token"].apply(lambda x: x is not None) & vec_df["context_vector"].apply(lambda x: type(x) == list)]
vec_df["text"] = vec_df.apply(
    lambda x: tag_filter_by_pos(x["context_token"], x["context_tag"]), axis=1
)

# %%
docs = vec_df["text"].tolist()
vecs = np.array(vec_df["context_vector"].tolist())
umap_model = UMAP(
    n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42
)
# umap_model = UMAP(n_components=5, n_neighbors=15, min_dist=0.0)
# hdbscan_model = HDBSCAN(min_samples=10, gen_min_span_tree=True, prediction_data=True)

topic_model = BERTopic(
    language="chinese",
    umap_model=umap_model,
    # hdbscan_model=hdbscan_model,
    min_topic_size=20,
    vectorizer_model=CountVectorizer(tokenizer=lambda x: x.split(" ")),
).fit(docs, vecs)

# %%
topic_model.save("/workdir/model_persistent/topics_model", serialization="safetensors", save_ctfidf=True)



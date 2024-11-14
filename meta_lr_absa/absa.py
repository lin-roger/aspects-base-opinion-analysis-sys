from elasticsearch import Elasticsearch, helpers
from transformers import AutoModelForCausalLM, AutoTokenizer, StaticCache
import eland as ed
import copy
import torch
from itertools import chain
import logging

FORMAT = "%(asctime)s %(filename)s %(levelname)s:%(message)s"
logging.basicConfig(
    level=logging.ERROR, format=FORMAT, filename="etl.log", filemode="a"
)

model_name = "Qwen/Qwen2.5-3B-Instruct-GPTQ-Int4"
model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto")

model.generation_config.temperature=None
model.generation_config.top_p=None
model.generation_config.top_k=None

tokenizer = AutoTokenizer.from_pretrained(model_name)
prompt_cache = StaticCache(
    config=model.config,
    batch_size=1,
    max_cache_len=1024,
    device="cuda",
    dtype=torch.float16,
)

def apply_template(user_input=None):
    messages = copy.deepcopy(base_messages)
    if user_input:
        messages.append({"role": "user", "content": user_input})
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True if user_input else False,
    )
    return prompt

def infer(prompt: str) -> list[list[dict]]:
    prompt = apply_template(prompt)
    new_inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    past_key_values = copy.deepcopy(prompt_cache)
    outputs = model.generate(
        **new_inputs,
        past_key_values=past_key_values,
        max_new_tokens=128,
        do_sample=False,
        num_beams=1,
    )
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(new_inputs.input_ids, outputs)
    ]

    map_dict ={
        "positive": 9,
        "neutral": 5,
        "negative": 1
    }

    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    try:
        return [{"a":aop.split(":")[0], "o":aop.split(":")[1], "p":map_dict[aop.split(":")[2]]} for aop in response.split(",")]
    except:
        return []

def aste_infer(texts: list[str]) -> list[list[dict]]:
    return [infer(text) if text else None for text in texts]
        
def comments_aste_infer(comments: list[dict]) -> list[dict]:
    comments = [
        {
            "content": comment["content"],
            "content_aste": infer(comment["content"])
        }
        for comment in comments
        if comment["content"]
    ]
    return comments

sys_prompt = """The output will be the aspect terms in the sentence followed by their describing words and sentiment polarity. if the aspect term or describing_word is not found in the sentence, the output will be empty. The sentiment polarity include: “positive”, “negative” and “neutral”. The output will be in the following format: aspect_term:describing_word:sentiment_polarity,aspect_term:describing_word:sentiment_polarity,..."""
demstrantion_set = [
    ("很夠味起司也很香。", "起司:很夠味:positive,起司:很香:positive"),
    ("這款沙拉真是我的愛。", "沙拉:我的愛:positive"),
    ("但可惜熱炒的品質不穩定，且價格也不平價。", "熱炒的品質:不穩定:negative,價格:不平價:negative"),
    ("但裡面的肉吃起來柴柴的。", "肉:柴柴的:negative"),
    ("鮮奶油和水果則是中規中矩。", "鮮奶油:中規中矩:neutral,水果:中規中矩:neutral"),
    ("小菜都沒有雷，但也沒有太印象深刻。", "小菜:沒有雷:neutral,小菜:沒有太印象深刻:neutral"),
]
tmp = [[{"role": "user", "content": i}, {"role": "assistant", "content": o}] for i, o in demstrantion_set]
base_messages = [{"role": "system", "content": sys_prompt}]
base_messages.extend(chain.from_iterable(tmp))

INITIAL_PROMPT = apply_template()
inputs_initial_prompt = tokenizer(INITIAL_PROMPT, return_tensors="pt").to(model.device)

with torch.no_grad():
    prompt_cache = model(
        **inputs_initial_prompt, past_key_values=prompt_cache
    ).past_key_values

idx_name = "docs"
client = Elasticsearch("http://host.docker.internal:9200", verify_certs=False, basic_auth=("elastic", "123456"))


backoff_count = 1
while True:
    ed_data = (
        ed.DataFrame(
            client,
            idx_name,
            columns=[
                "status_code",
                "link",
                "title",
                "title_aste",
                "date",
                "context",
                "context_aste",
                "comments",
            ],
        )
        .query("status_code == 'UN_ASTE' | status_code == 'ASTE_BY_TRANDITIONAL_NLP'")
        .head(5)
    )
    if not ed_data.empty:
        backoff_count = 1
        print("Processing data")
        try:
            pd_data = ed.eland_to_pandas(ed_data)
            pd_data["status_code"] = "ASTE_BY_QWEN"
            pd_data["title_aste"] = aste_infer(pd_data["title"].values)
            pd_data["context_aste"] = aste_infer(pd_data["context"].values)
            pd_data["comments"] = pd_data["comments"].apply(comments_aste_infer)
        except Exception as e:
            print("Error in processing data")
            logging.error("Error in processing data")
            logging.exception(e)
            logging.error("ID: %s", str(list(pd_data.index)))
            break

        print("Updating data")

        # buf = pd_data.to_json(date_format="iso")
        # parsed = loads(buf)
        # print(parsed)
        # break

        try:
            # ed.pandas_to_eland(pd_data, client, "dcard", es_if_exists="append", es_type_overrides={'comments':'nested', 'title_aste':'nested', 'context_aste':'nested'})
            for idx, data in pd_data.iterrows():
                client.update(
                    index=idx_name,
                    id=idx,
                    body={
                        "doc": {
                            "status_code": data["status_code"],
                            "title_aste": data["title_aste"],
                            "context_aste": data["context_aste"],
                            "comments": data["comments"],
                        },
                    },
                )
        except Exception as e:
            print("Error in updating data")
            logging.error("Error in updating data")
            logging.exception(e)
            break

        print("Data processed")

    else:
        logging.info("No data to process")
        time.sleep(5**backoff_count)
        if backoff_count < 4:
            backoff_count += 1

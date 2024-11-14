settin_body = {
    "index": {
        "default_pipeline": "tencentbac_conan_embedding_pipe",
        "analyze": {
            "max_token_count": 100000,
        },
        "analysis": {
            "analyzer": {
                "ik_smart_plus": {
                    "type": "custom",
                    "tokenizer": "ik_smart",
                    "filter": ["synonym"],
                },
                "ik_max_word_plus": {
                    "type": "custom",
                    "tokenizer": "ik_max_word",
                    "filter": ["synonym"],
                },
            },
            "filter": {
                "synonym": {
                    "type": "synonym",
                    "synonyms_path": "analysis-ik/dict/zh_synonym.txt",
                }
            },
        },
    }
}

mapping_body = {
    "properties": {
        "status_code": {"type": "keyword"},
        "platform": {"type": "keyword"},
        "borad": {"type": "keyword"},
        "link": {"type": "keyword", "index": False},
        "title": {
            "type": "text",
            "analyzer": "ik_max_word_plus",
            "search_analyzer": "ik_smart_plus",
        },
        "title_aste": {
            "type": "nested",
            "properties": {
                "a": {"type": "keyword"},
                "o": {"type": "keyword"},
                "p": {"type": "float"},
            },
        },
        "title_vector": {"type": "dense_vector"},
        "date": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS"},
        "crawl_time": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS"},
        "context": {
            "type": "text",
            "analyzer": "ik_max_word_plus",
            "search_analyzer": "ik_smart_plus",
        },
        "context_aste": {
            "type": "nested",
            "properties": {
                "a": {"type": "keyword"},
                "o": {"type": "keyword"},
                "p": {"type": "keyword"},
            },
        },
        "context_vector": {"type": "dense_vector"},
        "comments": {
            "type": "nested",
            "properties": {
                "username": {
                    "type": "text",
                    "analyzer": "ik_max_word_plus",
                    "search_analyzer": "ik_smart_plus",
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word_plus",
                    "search_analyzer": "ik_smart_plus",
                },
                "content_aste": {
                    "type": "nested",
                    "properties": {
                        "a": {"type": "keyword"},
                        "o": {"type": "keyword"},
                        "p": {"type": "float"},
                    },
                },
                "date": {"type": "date", "format": "yyyy-MM-dd HH:mm:ss.SSS"},
            },
        },
    }
}
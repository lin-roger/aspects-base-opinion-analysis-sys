# FROM python:3.11
FROM huggingface/transformers-quantization-latest-gpu:latest


WORKDIR /workdir
COPY ./.devcontainer ./.devcontainer

RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install -r ./.devcontainer/requirements.txt

# RUN python3 -m pip install elasticsearch \
#     && pip install --no-deps bertopic \
#     && pip install numpy hdbscan umap-learn pandas scikit-learn tqdm plotly pyyaml safetensors

RUN python3 -m pip install elasticsearch eland \
    && python3 -m pip install bertopic 

RUN python3 -m pip install streamlit-keyup

# RUN pip install \
#     --extra-index-url=https://pypi.nvidia.com \
#     "cudf-cu11==24.10.*" "dask-cudf-cu11==24.10.*" "cuml-cu11==24.10.*" \
#     "cugraph-cu11==24.10.*" "nx-cugraph-cu11==24.10.*" "cuspatial-cu11==24.10.*" \
#     "cuproj-cu11==24.10.*" "cuxfilter-cu11==24.10.*" "cucim-cu11==24.10.*" \
#     "pylibraft-cu11==24.10.*" "raft-dask-cu11==24.10.*" "cuvs-cu11==24.10.*" \
#     "nx-cugraph-cu11==24.10.*"

EXPOSE 8501

COPY . .

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
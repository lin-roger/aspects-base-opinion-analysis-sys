# FROM python:3-slim
# FROM python:3.11
# FROM python:3.11-slim
FROM huggingface/transformers-quantization-latest-gpu:latest

WORKDIR /workdir
COPY ./.devcontainer/requirements.txt ./.devcontainer/requirements.txt

# Install pip requirements
# COPY requirements.txt .
RUN python3 -m pip install --upgrade pip \
    && python3 -m pip install -r ./.devcontainer/requirements.txt

RUN python3 -m pip install elasticsearch \
    && python3 -m pip install eland \
    && python3 -m pip install bertopic

# RUN pip install \
#     --extra-index-url=https://pypi.nvidia.com \
#     "cudf-cu11==24.10.*" "dask-cudf-cu11==24.10.*" "cuml-cu11==24.10.*" \
#     "cugraph-cu11==24.10.*" "nx-cugraph-cu11==24.10.*" "cuspatial-cu11==24.10.*" \
#     "cuproj-cu11==24.10.*" "cuxfilter-cu11==24.10.*" "cucim-cu11==24.10.*" \
#     "pylibraft-cu11==24.10.*" "raft-dask-cu11==24.10.*" "cuvs-cu11==24.10.*" \
#     "nx-cugraph-cu11==24.10.*"

COPY . .

# CMD ["tail", "-f", "/dev/null"]
CMD ["python3", "aste_etl.py"]

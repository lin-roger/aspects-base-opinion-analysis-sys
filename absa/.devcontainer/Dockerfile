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

COPY . .

# CMD ["tail", "-f", "/dev/null"]
CMD ["python3", "aste_etl.py"]

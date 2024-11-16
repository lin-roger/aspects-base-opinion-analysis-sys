FROM python:3.11

WORKDIR /workdir
COPY ./.devcontainer ./.devcontainer

RUN python -m pip install --upgrade pip \
    && python -m pip install -r ./.devcontainer/requirements.txt

# RUN python -m pip install elasticsearch \
#     && pip install --no-deps bertopic \
#     && pip install numpy hdbscan umap-learn pandas scikit-learn tqdm plotly pyyaml safetensors

RUN python -m pip install elasticsearch \
    && python -m pip install bertopic 

RUN python -m pip install streamlit-keyup

EXPOSE 8501

COPY . .

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
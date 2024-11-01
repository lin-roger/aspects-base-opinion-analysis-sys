FROM python:3.11

WORKDIR /workdir
COPY . .

RUN python -m pip install --upgrade pip \
    && python -m pip install -r ./.devcontainer/requirements.txt

RUN python -m pip install elasticsearch \
    && python -m pip install eland

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "Home.py", "--server.port=8501", "--server.address=0.0.0.0"]
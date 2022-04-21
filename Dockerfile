FROM python:3.9-slim-bullseye
WORKDIR /Third-Party-Audit-GM-UI

COPY ['requirements.txt', "./"]

RUN \
    apt-get update -y && \
    python -m venv ./venv && \
    ./venv/bin/pip install --upgrade pip && \
    ./venv/bin/pip install --no-cache-dir -r ./requirements.txt


CMD streamlit run interface.py


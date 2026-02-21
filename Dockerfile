FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY localdeamon/ ./localdeamon/
COPY spellbook/ ./spellbook/
COPY tools/ ./tools/

RUN chmod +x tools/*.sh

ENV HOST_GET_URL=http://scraper:8000
ENV HOST_WEB_SEARCH=http://search:8001

ENTRYPOINT ["python", "main.py"]

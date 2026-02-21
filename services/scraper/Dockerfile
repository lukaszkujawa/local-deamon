FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install --with-deps chromium

COPY scraper.py .

ENV SCRAPER_HOST=0.0.0.0
ENV SCRAPER_PORT=8000

EXPOSE 8000

CMD ["python", "scraper.py"]

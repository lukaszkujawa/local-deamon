FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY search.py .
COPY providers/ ./providers/

ENV SEARCH_HOST=0.0.0.0
ENV SEARCH_PORT=8001

EXPOSE 8001

CMD ["python", "search.py"]

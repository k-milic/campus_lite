FROM python:3.9-slim

WORKDIR /campus-lite

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_APP=run.py

CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
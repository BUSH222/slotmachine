FROM python:3.11.9-slim

COPY requirements.txt requirements.txt
RUN pip install PyPI
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc
    
RUN pip install -r requirements.txt

COPY . .

CMD [ "python", "main.py" ]
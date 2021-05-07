FROM python:3.8-slim as build

RUN apt-get update && apt-get install -y gcc g++ zip

COPY requirements.txt /

RUN pip3 install -r requirements.txt

# stage 2

FROM python:3.8-slim as base

COPY --from=build /usr/bin/unzip /usr/bin/unzip

COPY --from=build /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/

COPY . /app

WORKDIR /app

RUN python3 -m unittest

ENTRYPOINT ["python3", "main.py", "config/quickfix.cfg", "config/subscriptions.txt", "data/"]

FROM python:3.11-slim
ADD requirements.txt /brevet/requirements.txt
WORKDIR /brevet
RUN pip install --no-cache-dir -r requirements.txt
ADD . /brevet

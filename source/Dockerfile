FROM python:3.13-slim

RUN mkdir /src
# include src files
ADD ./main.py /src
ADD ./MIP /src/MIP

RUN apt-get update && apt-get install -y --no-install-recommends coinor-cbc coinor-libcbc-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyomo numpy

CMD ["python", "/src/main.py"]
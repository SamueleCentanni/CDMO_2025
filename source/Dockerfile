FROM python:3.13-slim
ADD ./MIP /MIP

RUN apt-get update && apt-get install -y --no-install-recommends coinor-cbc coinor-libcbc-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyomo numpy

CMD ["python", "/MIP/STS_MILP.py"]
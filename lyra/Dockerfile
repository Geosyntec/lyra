
From redis:5.0.9-alpine3.11 as redis
COPY redis.conf /redis.conf
CMD ["redis-server", "/redis.conf"]


FROM python:3.7-alpine3.11 as flower
RUN apk add --no-cache ca-certificates && update-ca-certificates
RUN pip install --no-cache-dir redis==3.5.2 flower==0.9.4
ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1
EXPOSE 5555
USER nobody
ENTRYPOINT ["flower"]


FROM continuumio/miniconda3:4.8.2 as base
COPY conda_env.yml /conda_env.yml
RUN conda env create -f conda_env.yml
RUN echo "source activate lyra" > ~/.bashrc
ENV PATH /opt/conda/envs/lyra/bin:$PATH

RUN conda init bash

COPY requirements_conda.txt /requirements_conda.txt
RUN conda install -y --file /requirements_conda.txt \
  --channel conda-forge --channel defaults

COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY requirements_test.txt /requirements_test.txt
RUN pip install -r /requirements_test.txt

CMD ["bash", "-c", "while true; do sleep 1; done"]

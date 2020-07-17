
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


FROM python:3.7-buster as builder
RUN apt-get update -y \
  && apt-get install -y --no-install-recommends libspatialindex-dev \ 
  && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /requirements.txt
COPY requirements_test.txt /requirements_test.txt
COPY requirements_server.txt /requirements_server.txt
RUN mkdir /core \
  && pip wheel \
    --wheel-dir=/core \
    -r /requirements.txt
RUN mkdir /tsts \
  && pip wheel \
    --wheel-dir=/tsts \
    -r /requirements_test.txt
RUN mkdir /serve \
  && pip wheel \
    --wheel-dir=/serve \
    -r /requirements_server.txt


## FROM continuumio/miniconda3:4.8.2 as core
## COPY conda_env.yml /conda_env.yml
## 
## RUN conda env create -f conda_env.yml
## RUN echo "source activate lyra" > ~/.bashrc
## ENV PATH /opt/conda/envs/lyra/bin:$PATH
## RUN conda init bash
## COPY requirements_conda.txt /requirements_conda.txt
## RUN conda install -y --file /requirements_conda.txt \
##   --channel conda-forge --channel defaults
## COPY requirements.txt /requirements.txt
## RUN pip install \
##   --no-index \
##   --no-cache-dir \
##   -r /requirements.txt 
## COPY ./lyra /lyra/lyra
## WORKDIR /lyra
## ENV PYTHONPATH=/lyra

FROM python:3.7-slim-buster as core
COPY --from=builder /core /core
COPY requirements.txt /requirements.txt
RUN apt-get update \
  && apt-get install -y --no-install-recommends graphviz=2.40.1-6 \ 
  && rm -rf /var/lib/apt/lists/* \ 
  && pip install \
    --no-index \
    --no-cache-dir \
    --find-links=/core \
    -r /requirements.txt \
    && rm -rf /core/* 
COPY ./lyra /lyra/lyra
WORKDIR /lyra
ENV PYTHONPATH=/lyra


FROM core as celeryworker
ENV C_FORCE_ROOT=1
COPY ./scripts/run-worker.sh /run-worker.sh
RUN chmod +x /run-worker.sh
CMD ["bash", "/run-worker.sh"]


FROM core as lyra
COPY --from=builder /serve /serve
COPY requirements_server.txt /requirements_server.txt
RUN pip install \
  --no-index \
  --no-cache-dir \
  --find-links=/serve \
  -r /requirements_server.txt \
  && rm -rf /serve/*
COPY gunicorn_conf.py /gunicorn_conf.py
COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh
COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh
COPY ./scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
EXPOSE 8888
EXPOSE 80
CMD ["bash", "/entrypoint.sh"]

FROM core as lyra-tests
COPY requirements_test.txt /requirements_test.txt
COPY --from=builder /tsts /tsts
RUN pip install \
  --no-index \
  --no-cache-dir \
  --find-links=/tsts \
  -r /requirements_test.txt \
  && rm -rf /tsts/*
## COPY ./scripts/run-tests.sh /run-tests.sh
## COPY .coveragerc /lyra/.coveragerc
## COPY mypy.ini /lyra/mypy.ini
## RUN chmod +x /run-tests.sh
## This will make the container wait, doing nothing, but alive
CMD ["bash", "-c", "while true; do sleep 1; done"]
EXPOSE 8888

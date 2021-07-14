
FROM redis:5.0.9-alpine3.11 as redis
COPY redis.conf /redis.conf
CMD ["redis-server", "/redis.conf"]


FROM python:3.7-alpine3.11 as flower
RUN apk add --no-cache ca-certificates && update-ca-certificates
RUN pip install --no-cache-dir redis==3.5.2 flower==0.9.4 celery==4.4.7
ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1
EXPOSE 5555
USER nobody
ENTRYPOINT ["flower"]


FROM python:3.7-slim-buster as core-runtime
RUN apt-get update -y \
    && apt-get install -y curl gnupg2 \ 
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update -y \
    && ACCEPT_EULA=y apt-get install -y --no-install-recommends graphviz libspatialindex-dev unixodbc msodbcsql17 mssql-tools \ 
    && rm -rf /var/lib/apt/lists/*
WORKDIR /lyra
ENV PYTHONPATH=/lyra
ENV PATH=/root/.local/bin:$PATH


FROM python:3.7-buster as builder
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends gcc g++ unixodbc-dev libspatialindex-dev \ 
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
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


FROM python:3.7-slim-buster as core-env
COPY --from=builder /core /core
COPY requirements.txt /requirements.txt
RUN pip install \
    --user \
    --no-index \
    --no-cache-dir \
    --find-links=/core \
    -r /requirements.txt \
    && rm -rf /core/*


FROM core-runtime as celeryworker
COPY --from=core-env /root/.local /root/.local
ENV C_FORCE_ROOT=1
COPY ./scripts/run-worker.sh /run-worker.sh
RUN chmod +x /run-worker.sh
CMD ["bash", "/run-worker.sh"]
COPY ./lyra /lyra/lyra


FROM core-env as test-env
COPY requirements_test.txt /requirements_test.txt
COPY --from=builder /tsts /tsts
RUN pip install \
    --user \
    --no-index \
    --no-cache-dir \
    --find-links=/tsts \
    -r /requirements_test.txt \
    && rm -rf /tsts/*


FROM core-runtime as lyra-tests
COPY --from=test-env /root/.local /root/.local
COPY .coveragerc /lyra/.coveragerc
## This will make the container wait, doing nothing, but alive
CMD ["bash", "-c", "while true; do sleep 1; done"]
EXPOSE 8888
COPY ./lyra /lyra/lyra


FROM core-env as server-env
COPY requirements_server.txt /requirements_server.txt
COPY --from=builder /serve /serve
RUN pip install \
    --user \
    --no-index \
    --no-cache-dir \
    --find-links=/serve \
    -r /requirements_server.txt \
    && rm -rf /serve/*


FROM core-runtime as lyra
COPY --from=server-env /root/.local /root/.local
COPY gunicorn_conf.py /gunicorn_conf.py
COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh
COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh
EXPOSE 8888
EXPOSE 80
COPY ./lyra /lyra/lyra

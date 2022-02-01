
FROM redis:6.2.6-alpine3.15 as redis
COPY redis.conf /redis.conf
CMD ["redis-server", "/redis.conf"]


FROM python:3.9-alpine3.15 as flower
RUN apk add --no-cache ca-certificates tzdata && update-ca-certificates
RUN pip install --no-cache-dir redis==4.1.0 flower==1.0.0 celery==5.2.3
ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1
ENV FLOWER_DATA_DIR=/data 
ENV PYTHONPATH=${FLOWER_DATA_DIR}
WORKDIR $FLOWER_DATA_DIR
# Add a user with an explicit UID/GID and create necessary directories
ENV IMG_USER=flower
RUN set -eux; \
    addgroup -g 1000 ${IMG_USER}; \
    adduser -u 1000 -G ${IMG_USER} ${IMG_USER} -D; \
    mkdir -p "$FLOWER_DATA_DIR"; \
    chown ${IMG_USER}:${IMG_USER} "$FLOWER_DATA_DIR"
USER ${IMG_USER}
VOLUME $FLOWER_DATA_DIR
# Default port
EXPOSE 5555
CMD ["celery", "flower"]


FROM python:3.9.10-slim-buster as core-runtime
RUN apt-get update -y \
    && apt-get install -y curl gnupg2 \ 
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update -y \
    && ACCEPT_EULA=y apt-get install -y --no-install-recommends graphviz libspatialindex-dev unixodbc msodbcsql17 mssql-tools \ 
    && rm -rf /var/lib/apt/lists/*
WORKDIR /lyra
ENV PYTHONPATH=/lyra
ENV PATH=/opt/venv/bin:$PATH


FROM python:3.9.10-buster as builder
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


FROM python:3.9.10-slim-buster as core-env
COPY --from=builder /core /core
COPY requirements.txt /requirements.txt
RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH=/opt/venv/bin:$PATH
RUN pip install \
    --no-index \
    --no-cache-dir \
    --find-links=/core \
    -r /requirements.txt \
    && rm -rf /core/*


FROM core-runtime as celeryworker
# Add a user with an explicit UID/GID and create necessary directories
ENV IMG_USER=celeryworker
RUN addgroup --gid 1000 ${IMG_USER} \
    && adduser --system --disabled-password --uid 1000 --gid 1000 ${IMG_USER} \
    && chown -R ${IMG_USER}:${IMG_USER} /lyra 
USER ${IMG_USER}
COPY --from=core-env --chown=${IMG_USER} /opt/venv /opt/venv
COPY --chown=${IMG_USER} ./scripts/run-worker.sh /run-worker.sh
RUN chmod gu+x /run-worker.sh
CMD ["bash", "/run-worker.sh"]
COPY --chown=${IMG_USER} ./lyra /lyra/lyra


FROM core-env as test-env
COPY requirements_test.txt /requirements_test.txt
COPY --from=builder /tsts /tsts
RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH=/opt/venv/bin:$PATH
RUN pip install \
    --no-index \
    --no-cache-dir \
    --find-links=/tsts \
    -r /requirements_test.txt \
    && rm -rf /tsts/*


FROM core-runtime as lyra-tests
COPY --from=test-env /opt/venv /opt/venv
COPY .coveragerc /lyra/.coveragerc
## This will make the container wait, doing nothing, but alive
CMD ["bash", "-c", "while true; do sleep 1; done"]
EXPOSE 8888
COPY ./lyra /lyra/lyra


FROM core-env as server-env
COPY requirements_server.txt /requirements_server.txt
COPY --from=builder /serve /serve
RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH=/opt/venv/bin:$PATH
RUN pip install \
    --no-index \
    --no-cache-dir \
    --find-links=/serve \
    -r /requirements_server.txt \
    && rm -rf /serve/*


FROM core-runtime as lyra
COPY --from=server-env /opt/venv /opt/venv
COPY gunicorn_conf.py /gunicorn_conf.py
COPY ./scripts/start.sh /start.sh
RUN chmod +x /start.sh
COPY ./scripts/start-reload.sh /start-reload.sh
RUN chmod +x /start-reload.sh
EXPOSE 8888
EXPOSE 80
COPY ./lyra /lyra/lyra


FROM python:3.9-buster as lyra-edge
RUN apt-get update -y \
    && apt-get install -y curl gnupg2 \ 
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends gcc g++ unixodbc-dev libspatialindex-dev \ 
    && ACCEPT_EULA=y apt-get install -y --no-install-recommends graphviz libspatialindex-dev unixodbc msodbcsql17 mssql-tools \ 
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt /requirements.txt
COPY requirements_test.txt /requirements_test.txt
RUN awk -F"==" '{print $1}' /requirements.txt /requirements_test.txt \
    > /requirements_edge.txt
RUN cat requirements_edge.txt
RUN pip install -r /requirements_edge.txt
WORKDIR /lyra
ENV PYTHONPATH=/lyra
COPY ./lyra /lyra/lyra


FROM lyra-edge as lyra-edge-tests
CMD ["bash", "-c", "while true; do sleep 1; done"]


FROM lyra-edge as celeryworker-edge
ENV C_FORCE_ROOT=1
COPY ./scripts/run-worker.sh /run-worker.sh
RUN chmod +x /run-worker.sh
CMD ["bash", "/run-worker.sh"]
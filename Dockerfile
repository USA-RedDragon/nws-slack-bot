FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN apk add --virtual .build-deps \
        build-base \
        geos-dev \
        proj-dev \
        gfortran \
        openblas-dev \
    && apk add \
        ca-certificates \
        curl \
        geos \
        proj \
        proj-util \
        s6 \
        openblas \
    && pip install -r requirements.txt \
    && apk del .build-deps \
    && rm -rf /tmp/* /var/cache/apk/*


COPY src/ src/
COPY scripts/ scripts/

RUN python -m scripts.generate_state_images --output /app/.states --all

ENV CONFIG_JSON ""

COPY rootfs/ /
RUN chmod a+x /init /etc/s6/*/run

EXPOSE 80

ENTRYPOINT ["/init"]

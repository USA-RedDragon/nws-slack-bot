FROM python:3.11-alpine

WORKDIR /app

RUN apk add --no-cache build-base proj-util geos-dev proj-dev

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY src/ src/

ENV CONFIG_JSON ""

COPY /entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENV PYTHONUNBUFFERED=1

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]

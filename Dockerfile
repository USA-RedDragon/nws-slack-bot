FROM python:3.11-alpine

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apk add --no-cache build-base proj-util geos-dev proj-dev curl

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY src/ src/
COPY scripts/ scripts/

RUN python -m scripts.generate_state_images --output /app/.states --all

ENV CONFIG_JSON ""

COPY /entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/entrypoint.sh"]

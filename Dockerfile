FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY src/ src/

ENV CONFIG_JSON ""

COPY /entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

ENTRYPOINT [ "/entrypoint.sh", "--", "python", "/app/src/main.py" ]

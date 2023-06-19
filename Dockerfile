FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

ENV CONFIG_JSON ""

COPY /entrypoint.sh /entrypoint.sh
RUN chmod a+x /entrypoint.sh

VOLUME [ "/app/data" ]

ENTRYPOINT [ "/entrypoint.sh" ]

FROM ghcr.io/usa-reddragon/python-gis:main@sha256:3303741dcb4c8fa0556f15a3fcaf8986031c94cccd9fbf7791c62e9c779fa72c

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt requirements.txt

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get update && \
    apt-get -y --no-install-recommends install \
      curl \
      s6 \
      cron \
      python3-aiohttp

RUN export DEBIAN_FRONTEND=noninteractive && \
    apt-get -y --no-install-recommends install \
      build-essential && \
    pip install -r requirements.txt && \
    apt-get remove -y \
      build-essential && \
    apt-get clean && rm -rf /tmp/setup /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY scripts/ scripts/

RUN python -m scripts.generate_all_images --output /app/.states -j64

ENV CONFIG_JSON ""

COPY rootfs/ /
RUN chmod a+x /init /etc/s6/*/run

RUN <<__EOF__
# Grab day 1 outlooks 5 minutes after each publishing time
# 0600Z
(crontab -l 2>/dev/null; echo "05 06 * * * sh -c 'cd /app && python -m src.spc_day1'") | crontab -
# 1300Z
(crontab -l 2>/dev/null; echo "05 13 * * * sh -c 'cd /app && python -m src.spc_day1'") | crontab -
# 1630Z
(crontab -l 2>/dev/null; echo "35 16 * * * sh -c 'cd /app && python -m src.spc_day1'") | crontab -
# 2000Z
(crontab -l 2>/dev/null; echo "05 20 * * * sh -c 'cd /app && python -m src.spc_day1'") | crontab -
# 0100Z
(crontab -l 2>/dev/null; echo "05 01 * * * sh -c 'cd /app && python -m src.spc_day1'") | crontab -

# Grab day 2 outlooks 5 minutes after each publishing time
# 1:00 AM CDT
(crontab -l 2>/dev/null; echo "05 06 * * * sh -c 'cd /app && python -m src.spc_day2 cdt'") | crontab -
# 1:00 AM CST
(crontab -l 2>/dev/null; echo "05 07 * * * sh -c 'cd /app && python -m src.spc_day2 cst'") | crontab -
# 1730Z
(crontab -l 2>/dev/null; echo "35 17 * * * sh -c 'cd /app && python -m src.spc_day2 utc'") | crontab -

# Grab day 3 outlooks 5 minutes after each publishing time
# 2:30 AM CDT
(crontab -l 2>/dev/null; echo "35 07 * * * sh -c 'cd /app && python -m src.spc_day3 cdt'") | crontab -
# 2:30 AM CST
(crontab -l 2>/dev/null; echo "35 08 * * * sh -c 'cd /app && python -m src.spc_day3 cst'") | crontab -

# Grab day 4-8 outlooks 5 minutes after the publishing time
# 4:00 AM CDT
(crontab -l 2>/dev/null; echo "05 09 * * * sh -c 'cd /app && python -m src.spc_day4-8 cdt'") | crontab -
# 4:00 AM CST
(crontab -l 2>/dev/null; echo "05 10 * * * sh -c 'cd /app && python -m src.spc_day4-8 cst'") | crontab -
__EOF__

COPY src/ src/

EXPOSE 80

ENTRYPOINT ["/init"]

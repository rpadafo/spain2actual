FROM node:22-bookworm-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

COPY package.json ./
RUN npm install --omit=dev --no-audit --no-fund

RUN pip install --no-cache-dir pandas openpyxl watchdog xlrd colorama pdfplumber

COPY conf/ .

CMD ["python", "-u", "automata.py"]
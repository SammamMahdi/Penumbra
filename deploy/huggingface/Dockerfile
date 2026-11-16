# Penumbra on Hugging Face Spaces (Docker SDK).
# The code comes from the public GitHub repository; the runtime data comes from a private Hugging Face dataset,
# read at build time with the DATA_TOKEN Space secret. Published by deploy/huggingface/publish.py.

FROM node:22-slim AS web
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
ARG REPO=https://github.com/SammamMahdi/Penumbra.git
ARG REF=main
RUN git clone --depth 1 --branch ${REF} ${REPO} /src
WORKDIR /src
RUN npm ci && npm run build && rm -rf node_modules .git

FROM python:3.12-slim
RUN useradd -m -u 1000 user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /home/user/app
COPY --from=web --chown=user /src /home/user/app
# Test-only packages (pytest, Playwright) are not needed to run the app.
RUN grep -vE '^(playwright|pytest)==' backend/requirements.txt > /tmp/requirements.txt \
 && pip install --no-cache-dir -r /tmp/requirements.txt huggingface_hub==0.36.2
COPY --chown=user fetch_data.py /home/user/fetch_data.py
USER user
ARG DATA_REPO=__DATA_REPO__
RUN --mount=type=secret,id=DATA_TOKEN,mode=0444,required=true \
    python /home/user/fetch_data.py "${DATA_REPO}"
EXPOSE 7860
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "7860"]

# The analysis environment, frozen: the same Python as the author's (3.11.18) and every package locked by SHA-256.
# It recomputes every number from the committed results; it trains nothing.
#
#   docker build -t pineau-rl .
#   docker run --rm -v "$PWD":/repo pineau-rl              # make verify: analyses, number checks, tests, byte-for-byte diff
#   docker run --rm -v "$PWD":/repo pineau-rl make check   # any other target of the Makefile
#
# The base image is pinned by digest (python:3.11-slim, Debian bookworm, Python 3.11.18, amd64 and arm64).
FROM python:3.11-slim@sha256:07d4824036af339fa1b6ef769cc99d9c10a141769538b52b3b597c84f7a7b535

RUN apt-get update && apt-get install -y --no-install-recommends make git && rm -rf /var/lib/apt/lists/*
COPY envs/analysis.lock /tmp/analysis.lock
RUN pip install --no-cache-dir --require-hashes -r /tmp/analysis.lock && rm /tmp/analysis.lock

# The repository is mounted at run time, not copied, so the image serves any commit.
WORKDIR /repo
RUN git config --global --add safe.directory /repo
ENV PY=python NICE= PYTHONDONTWRITEBYTECODE=1
CMD ["make", "verify"]

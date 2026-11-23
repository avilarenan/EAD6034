FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Pacotes públicos do Debian, suficientes para executar o exercício em R.
RUN apt-get update \
    && apt-get install -y --no-install-recommends r-base-core r-cran-urca r-cran-tseries \
    && rm -rf /var/lib/apt/lists/*

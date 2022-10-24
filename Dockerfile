FROM python:3.10.4
RUN python3 --version
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.1.14 \
    APP_PORT=8000

# System deps:
RUN pip install "poetry==$POETRY_VERSION"

COPY . ./

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

ENTRYPOINT [ "python" , "./main.py"]
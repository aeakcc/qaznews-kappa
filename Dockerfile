# Two targets from one base, so tests run on exactly the interpreter the tool ships with.
#   docker build --target test -t qaznews-kappa:test .   pytest, ruff and the example batches
#   docker build -t qaznews-kappa .                       runtime image (last stage)
FROM python:3.12-slim AS base
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

FROM base AS test
RUN pip install -e ".[dev]"
COPY tests ./tests
COPY examples ./examples
CMD ["pytest"]

FROM base AS runtime
RUN pip install . && useradd --create-home kappa
USER kappa
ENTRYPOINT ["qaznews-kappa"]
CMD ["--help"]

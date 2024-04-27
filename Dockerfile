ARG PYTHON_BASE=3.12-slim

FROM python:$PYTHON_BASE AS builder

RUN pip install -U pdm
COPY pyproject.toml pdm.lock README.md /project/
COPY src/ /project/src

WORKDIR /project
RUN pdm install --check --prod --no-editable

FROM python:$PYTHON_BASE

COPY --from=builder /project/.venv/ /project/.venv
ENV PATH="/project/.venv/bin:$PATH"

COPY . /project/app
WORKDIR /project/app
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "80"]

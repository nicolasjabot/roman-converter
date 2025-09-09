FROM ghcr.io/astral-sh/uv:python3.12-bookworm

WORKDIR /cli-roman
COPY . .


RUN uv sync

CMD [".venv/bin/uvicorn", "src.roman_api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
FROM ghcr.io/astral-sh/uv:latest

WORKDIR /app

COPY pyproject.toml .

RUN ["uv", "sync"]

COPY . .

EXPOSE 8000

CMD ["uv", "run", "main.py"]

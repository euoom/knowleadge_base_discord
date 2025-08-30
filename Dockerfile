FROM astral/uv:bookworm-slim

WORKDIR /app

COPY pyproject.toml .

RUN ["uv", "sync"]

COPY . .

EXPOSE 8000

CMD ["uv", "run", "main.py"]

# Astral의 공식 uv 이미지를 사용합니다. (Python 3.11 포함)
FROM ghcr.io/astral-sh/uv:latest

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 정의 파일을 먼저 복사합니다.
COPY pyproject.toml ./

# uv를 사용하여 의존성을 설치합니다.
RUN uv pip install --system -r pyproject.toml

# 나머지 소스 코드를 복사합니다.
COPY . .

# 컨테이너가 사용할 포트를 명시합니다.
EXPOSE 8000

# uvicorn 서버를 실행합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

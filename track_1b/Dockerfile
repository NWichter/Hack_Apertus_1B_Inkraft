FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir . "pytest>=8,<9"

COPY tests ./tests
COPY data ./data
COPY run.sh ./

ENTRYPOINT ["sh", "/app/run.sh"]
CMD ["replay"]

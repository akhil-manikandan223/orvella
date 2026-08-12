# Dev-oriented image: installs dev deps (ruff/pytest included) so lint/test can
# also be run inside the container. A production-hardened multi-stage build
# (base.txt only) is deferred to Phase 8 (Deployment).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 1000 app && useradd --uid 1000 --gid app --create-home app

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY . .
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

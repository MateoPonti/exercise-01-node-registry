# TODO: Write a production-ready Dockerfile
#
# All of these are tested by the grader:
#
# [ ] Multi-stage build (2+ FROM instructions)
# [ ] Base image: python:3.14-slim (pinned version, no :latest)
# [ ] Copy requirements.txt and pip install BEFORE copying source code (layer caching)
# [ ] Run as a non-root USER
# [ ] EXPOSE 8080
# [ ] HEALTHCHECK instruction
# [ ] No hardcoded secrets (no ENV PASSWORD=..., no ENV SECRET_KEY=...)
# [ ] Final image under 200MB
#
# Start command: uvicorn src.app:app --host 0.0.0.0 --port 8080
# ---- Build stage ----
FROM python:3.14-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- Final stage ----
FROM python:3.14-slim

# Create a non-root user to run the application
RUN useradd --create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Bring in the packages installed in the builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy dependency manifest first (cache layer), then app code
COPY requirements.txt .
COPY src/ ./src/

ENV PATH="/home/appuser/.local/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["uvicorn", "app:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8080"]
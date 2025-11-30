FROM python:3.13-slim

WORKDIR /app

# Install dependencies
# We list them explicitly here to avoid needing a full build system setup for pyproject.toml
# if it lacks the [build-system] table.
RUN pip install --no-cache-dir \
    fastapi>=0.120.4 \
    "uvicorn[standard]>=0.30.0" \
    pydantic>=2.12.3 \
    python-dotenv>=1.2.1 \
    requests>=2.32.5

# Copy source code
COPY . /app

# Ensure stdout/stderr are unbuffered for immediate log visibility
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application with explicit log level
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]

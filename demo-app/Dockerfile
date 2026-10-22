# CISE demo app Dockerfile — minimal stdlib-only service.
# Builds directly from the source tree (src layout, pyproject.toml), so the
# container-scan job (`docker build -t <tag> ./demo-app`) works out of the box
# on GitHub-hosted runners with no pre-built wheel checked in.

FROM python:3.11-slim-bookworm

RUN useradd --create-home --home-dir /app app \
    && chown -R app:app /app

WORKDIR /app

# Install the project (editable dev install, then the same for the image).
COPY --chown=app:app . /app
RUN pip install --no-cache-dir -e ".[dev]"

USER app
EXPOSE 8000
CMD ["demo_app.main"]

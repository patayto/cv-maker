FROM python:3.13-slim

WORKDIR /app

# Install dependencies from the uv lockfile — the single source of truth.
# (A hand-maintained requirements.txt drifted out of date before; don't reintroduce one.)
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv export --frozen --no-dev --no-emit-project --format requirements-txt -o requirements.txt \
    && pip install --no-cache-dir -r requirements.txt \
    && rm requirements.txt

# CV/cover-letter PDF generation needs lualatex + xelatex (TeX Live adds ~2GB;
# remove this layer for a slim image without document generation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-luatex texlive-xetex texlive-latex-extra texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Copy backend source
COPY backend/ ./backend/

WORKDIR /app/backend

RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 8192
ENTRYPOINT ["/app/backend/entrypoint.sh"]

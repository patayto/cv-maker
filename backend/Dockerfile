FROM python:3.13-slim

WORKDIR /app

# Install Python dependencies first (layer cached unless requirements.txt changes)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright's Chromium browser and its system dependencies
RUN playwright install chromium --with-deps

# Copy backend source
COPY backend/ ./backend/

WORKDIR /app/backend

RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 8192
ENTRYPOINT ["/app/backend/entrypoint.sh"]

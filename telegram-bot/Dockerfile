FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all bot code (bot, worker, batcher)
COPY . .

# Default: Run bot (worker runs in separate container)
CMD ["python", "bot.py"]

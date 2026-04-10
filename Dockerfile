FROM python:3.12-slim

# Prevent Python issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 🔑 Add Django environment variables
ENV SECRET_KEY=super-secret-key
ENV DEBUG=False
ENV ALLOWED_HOSTS=*
ENV DJANGO_SETTINGS_MODULE=mysite.settings

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    libasound2 \
    libportaudio2 \
    portaudio19-dev \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt gunicorn

# Copy project
COPY . .

# 🔥 Ensure static folder exists (prevents crash)
RUN mkdir -p /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Run migrations + server
CMD ["sh", "-c", "python manage.py migrate && gunicorn mysite.wsgi:application --bind 0.0.0.0:${PORT:-8000}"]

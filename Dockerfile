FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1 \
    libasound2 \
    libportaudio2 \
    portaudio19-dev \
    ffmpeg \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt gunicorn

COPY . .

# ✅ FIXED HERE
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]

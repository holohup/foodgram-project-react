FROM python:3.7-slim
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV MAIN_HOST http://ondeletecascade.ru
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir
COPY . .
CMD ["gunicorn", "foodgram.wsgi:application", "--bind", "0:8000"]

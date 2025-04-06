FROM python

WORKDIR /app

COPY /app /app/app
COPY /requirements.txt /.env /app/

RUN pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
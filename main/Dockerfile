FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    sqlalchemy \
    pwdlib \
    pydantic \
    psycopg2-binary \
    python-jose \
    cryptography \
    dotenv 

EXPOSE 8080

CMD ["uvicorn","controller:application","--host", "0.0.0.0", "--port", "8080"]
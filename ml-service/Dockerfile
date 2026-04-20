FROM isp-backend:v1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir numpy==1.26.0 pydantic==2.5.0

COPY predictor.py .

EXPOSE 8001

CMD ["uvicorn", "predictor:app", "--host", "0.0.0.0", "--port", "8001"]

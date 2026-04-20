FROM isp-backend:v1

WORKDIR /app

RUN pip install --no-cache-dir requests==2.31.0

COPY controller.py .

CMD ["python", "controller.py"]

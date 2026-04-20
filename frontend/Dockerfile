FROM isp-backend:v1

WORKDIR /app

COPY dashboard/build /app/build

COPY serve.py .

EXPOSE 3000

CMD ["python", "serve.py"]

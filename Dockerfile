FROM python:3.12-slim

WORKDIR /app

COPY app/ /app
COPY entrypoint.sh /entrypoint.sh

RUN pip install flask \
 && chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]

FROM python:3.11.0-alpine
COPY custom_exporter.py /app/custom_exporter/custom_exporter.py
WORKDIR /app
COPY requirements.txt ./
RUN apk update && apk add --no-cache tzdata bash bash-completion bash-doc mysql-client gcc libc-dev mariadb-dev mariadb-client && ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo "Asia/Shanghai" > /etc/timezone
RUN pip install --no-cache-dir -r requirements.txt 
WORKDIR /app/custom_exporter
CMD ["python","custom_exporter.py"]
EXPOSE 9111

FROM registry.access.redhat.com/ubi9/ubi:9.4

RUN dnf install -y python3 python3-pip && dnf clean all && \
    useradd -m appuser

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8080

CMD ["python3", "app.py"]

FROM python:3.11-slim

WORKDIR /opt/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
# Hidden dir with the "leaked" host creds the attacker finds post-RCE
COPY .internal/ .internal/

# Deliberately run as root inside the container so the pickle RCE
# gives full control of the container filesystem (simulates a
# common real-world misconfig of containerized internal tools).
EXPOSE 5000
CMD ["python", "app.py"]

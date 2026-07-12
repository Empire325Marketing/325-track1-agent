FROM python:3.11-slim

LABEL org.opencontainers.image.title="325 Track 1 Agent"
LABEL org.opencontainers.image.description="Hybrid Token-Efficient Routing Agent — AMD Developer Hackathon Act II"
LABEL org.opencontainers.image.authors="Milton J Acosta III <support@empire325marketing.com>"
LABEL org.opencontainers.image.vendor="Empire325Marketing"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY agent.py .

RUN mkdir -p /input /output \
    && python3 -m py_compile /app/agent.py

CMD ["python3", "/app/agent.py"]

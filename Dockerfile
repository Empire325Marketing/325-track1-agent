FROM python:3.11-slim

LABEL org.opencontainers.image.title="325 Track 1 Agent"
LABEL org.opencontainers.image.description="Hybrid Token-Efficient Routing Agent — AMD Developer Hackathon Act II"
LABEL org.opencontainers.image.authors="Milton J Acosta III <support@empire325marketing.com>"
LABEL org.opencontainers.image.vendor="Empire325Marketing"

# Build args
ARG FIREWORKS_API_KEY
ENV FIREWORKS_API_KEY=${FIREWORKS_API_KEY}

# Runtime env
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1/chat/completions
ENV ALLOWED_MODELS=accounts/fireworks/models/llama-v3p1-405b-instruct

# Create non-root user
RUN useradd --create-home --shell /bin/bash agent

WORKDIR /app

# Copy only what's needed
COPY agent.py .
COPY test_tasks.json .

# Make I/O dirs
RUN mkdir -p /input /output && chown -R agent:agent /app /input /output

USER agent

# Test that local solvers work without API key
RUN python3 -c "from agent import try_local; ans, name, t = try_local('What is 2+2?'); assert ans == '4', f'Math solver failed: {ans}'; print('Local solvers: OK')"
RUN python3 -c "from agent import solve_sentiment; assert solve_sentiment('I love this') == 'positive'; print('Sentiment: OK')"
RUN python3 -c "from agent import solve_counting; assert solve_counting(\"How many characters are in 'hello'?\") == '5'; print('Counting: OK')"

ENTRYPOINT ["python3", "agent.py"]

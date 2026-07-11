FROM python:3.11-alpine

LABEL org.opencontainers.image.title="325 Track 1 Agent"
LABEL org.opencontainers.image.description="Hybrid Token-Efficient Routing Agent — AMD Developer Hackathon Act II"
LABEL org.opencontainers.image.authors="Milton J Acosta III <support@empire325marketing.com>"
LABEL org.opencontainers.image.vendor="Empire325Marketing"

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FIREWORKS_BASE_URL=https://api.fireworks.ai/inference/v1/chat/completions
ENV ALLOWED_MODELS=accounts/fireworks/models/llama-v3p1-405b-instruct

RUN adduser -D -h /app agent

WORKDIR /app
COPY agent.py .
COPY test_tasks.json .

RUN mkdir -p /input /output && chmod 777 /output /input && chown -R agent:agent /app /input /output

USER agent

# Verify local solvers work (no deps needed)
RUN python3 -c "from agent import try_local; ans, name, t = try_local('What is 2+2?'); assert ans == '4', f'Failed: {ans}'; print('OK: math')"
RUN python3 -c "from agent import solve_sentiment; assert solve_sentiment('I love this') == 'Positive'; print('OK: sentiment')"
RUN python3 -c "from agent import solve_unit_conversion; assert solve_unit_conversion('10 inches to cm') == '25.4'; print('OK: units')"
RUN python3 -c "from agent import solve_temperature; assert solve_temperature('100 Celsius to Fahrenheit') == '212.0'; print('OK: temp')"
RUN python3 -c "from agent import solve_simple_facts; assert solve_simple_facts('capital of france') == 'Paris'; print('OK: facts')"

ENTRYPOINT ["python3", "agent.py"]

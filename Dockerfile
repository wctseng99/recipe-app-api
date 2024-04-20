FROM python:3.9-alpine3.13
lABEL maintainer="wctseng.com"

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Set work directory
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# Install dependencies
ARG DEV=false
RUN python -m venv /py && \ 
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ]; \
    then /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    adduser \
    --disabled-password \
    --no-create-home \
    django-user

# Set environment variables
ENV PATH="/py/bin:$PATH"

# Switch to non-root user
USER django-user
FROM python:3.6
LABEL maintainer "Michael Lin <terragnome@gmail.com>"

# Create working directory
RUN apt-get update
RUN mkdir /app
WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV FLASK_ENV="docker"

# Expose port 5000
EXPOSE 5000

# Populate the events db
# RUN sh scripts/sync.sh

ENTRYPOINT ["python"]
CMD ["app.py"]
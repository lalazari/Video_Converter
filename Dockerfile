FROM alpine
MAINTAINER Michalis Lazaridis <Michalis.Lazaridis@iti.gr>, Lazaros Lazaridis <lazlazari@iti.gr>
RUN apk upgrade -U \
 && apk add bash python py-pip ca-certificates ffmpeg \
 && apk add netcat-openbsd \
 && rm -rf /var/cache/*
RUN mkdir -p /video_converter
COPY . /video_converter/

WORKDIR /video_converter
COPY requirements.txt /video_converter/requirements.txt
RUN pip install --no-cache-dir -r /video_converter/requirements.txt

CMD ["python", "run_service.py", "9876"]



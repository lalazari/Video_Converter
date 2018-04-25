FROM alpine
MAINTAINER Michalis Lazaridis <Michalis.Lazaridis@iti.gr>, Lazaros Lazaridis <lazlazari@iti.gr>
RUN apk upgrade -U \
 && apk add bash build-base python-dev python py-pip ca-certificates ffmpeg py-numpy jpeg-dev zlib-dev \
 && apk add netcat-openbsd \
 && rm -rf /var/cache/*
RUN mkdir -p /video_converter
COPY requirements.txt /video_converter/requirements.txt
RUN pip install --no-cache-dir -r /video_converter/requirements.txt

COPY . /video_converter/

ENV LIBRARY_PATH=/lib:/usr/lib
WORKDIR /video_converter

CMD ["python", "run_service.py", "9877"]

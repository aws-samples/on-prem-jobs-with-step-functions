FROM python:alpine3.20

ENV ENDPOINT=a3hizaz7f8jraw-ats.iot.eu-west-1.amazonaws.com
ENV CA_FILE=certs/root-CA.crt
ENV DEVICE_CERT=certs/cert.pem
ENV PRIVATE_KEY=certs/priv.key
ENV CLIENT_ID=mqtt-container-client
ENV SUBSCRIBE_TOPIC=tenant1/to/worker
ENV SUBMIT_TOPIC=tenant1/to/lambda

RUN apk update \
  && apk add --update alpine-sdk make cmake git \
  && mkdir crt-workspace \
  && cd crt-workspace \
  && git clone https://github.com/awslabs/aws-crt-python.git \
  && cd aws-crt-python \
  && latest_tag=$(git describe --tags --abbrev=0) \
  && git checkout tags/$latest_tag -b $latest_tag \
  && git submodule update --init --recursive \
  && sed -i "s/__version__ = '1.0.0.dev0'/__version__ = '${latest_tag}'/" awscrt/__init__.py \
  && python3 -m pip install . \
  && mkdir /mqtt

COPY . /mqtt
WORKDIR /mqtt
RUN pip install -r requirements.txt

ENTRYPOINT [ "python3", "onPremWorker.py", "--ca_file", "${CA_FILE}", "--cert", "${DEVICE_CERT}", "--key", "${PRIVATE_KEY}", "--client_id", "${CLIENT_ID}", "--topic", "${SUBSCRIBE_TOPIC}",  "--endpoint", "${ENDPOINT}}" ]

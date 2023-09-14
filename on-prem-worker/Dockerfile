FROM python:alpine3.11

ARG ENDPOINT=<IOT_CORE_ENDPOINT_URL>
ARG CA_FILE=certs/root-CA.crt
ARG DEVICE_CERT=certs/cert.pem
ARG PRIVATE_KEY=certs/priv.key
ARG CLIENT_ID=mqtt-container-client
ARG SUBSCRIBE_TOPIC=tenant1/to/worker
ARG SUBMIT_TOPIC=tenant1/to/lambda

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

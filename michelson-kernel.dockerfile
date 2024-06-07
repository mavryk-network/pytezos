FROM python:3.11-alpine3.17 AS compile-image
RUN apk add --update --no-cache \
	build-base \
	libtool \
	autoconf \
	automake \
	python3-dev \
	libffi-dev \
	gmp-dev \
	libsodium-dev \
	libsecp256k1-dev

RUN mkdir /tmp/secp256k1 \
	&& cd /tmp \
	&& wget https://github.com/bitcoin-core/secp256k1/archive/refs/tags/v0.2.0.tar.gz -O /tmp/secp256k1.tar.gz \
	&& tar -xzf /tmp/secp256k1.tar.gz -C /tmp/secp256k1 --strip-components=1 \
	&& cd /tmp/secp256k1 \
	&& ./autogen.sh \
	&& ./configure

RUN python -m venv --without-pip --system-site-packages /opt/pymavryk \
    && mkdir -p /opt/pymavryk/src/pymavryk/ \
    && touch /opt/pymavryk/src/pymavryk/__init__.py \
    && mkdir -p /opt/pymavryk/src/michelson_kernel/ \
    && touch /opt/pymavryk/src/michelson_kernel/__init__.py
WORKDIR /opt/pymavryk
ENV PATH="/opt/pymavryk/bin:$PATH"
ENV PYTHON_PATH="/opt/pymavryk/src:$PATH"

COPY pyproject.toml requirements.txt README.md /opt/pymavryk/

RUN /usr/local/bin/pip install --prefix /opt/pymavryk --no-cache-dir --disable-pip-version-check --no-deps -r /opt/pymavryk/requirements.txt -e .

FROM python:3.11-alpine3.17 AS build-image
RUN apk add --update --no-cache \
	binutils \
	gmp-dev \
	libsodium-dev \
	libsecp256k1-dev

RUN adduser -D pymavryk
USER pymavryk
ENV PATH="/opt/pymavryk/bin:$PATH"
ENV PYTHONPATH="/home/pymavryk:/home/pymavryk/src:/opt/pymavryk/src:/opt/pymavryk/lib/python3.11/site-packages:$PYTHONPATH"
WORKDIR /home/pymavryk/
ENTRYPOINT [ "/opt/pymavryk/bin/jupyter-notebook", "--port=8888", "--ip=0.0.0.0" , "--no-browser", "--no-mathjax" ]
EXPOSE 8888

COPY --chown=pymavryk --from=compile-image /opt/pymavryk /opt/pymavryk
COPY --chown=pymavryk . /opt/pymavryk

RUN michelson-kernel install

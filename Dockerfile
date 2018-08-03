#
# Create an Ubuntu image with a minimal GDAL 2.3.1, including the latest version of libzstd to support 
# zstd compression.
#
# Based on the GDAL Docker images by Cayetano Benavent, available at https://github.com/GeographicaGS/Docker-GDAL2
#

FROM ubuntu:xenial

ENV ROOTDIR /usr/local/
ENV GDAL_VERSION master
ENV ZSTD_VERSION 1.3.5

# Load assets
WORKDIR $ROOTDIR/

# Install basic dependencies
RUN apt-get update -y && apt-get install -y \
    software-properties-common \
    python3-software-properties \
    build-essential \
    python3-dev \
    python3-numpy \
    libcurl4-gnutls-dev \
    libproj-dev \
    liblzma-dev \
    wget \
    bash-completion \
    cmake \
    linux-tools-common \
    linux-tools-generic \
    linux-tools-$(uname -r)

# Create root src directory
RUN mkdir -p $ROOTDIR/src

# Download, compile and install libzstd
RUN wget -q -O $ROOTDIR/src/zstd-${ZSTD_VERSION}.tar.gz https://github.com/facebook/zstd/archive/v${ZSTD_VERSION}.tar.gz \
    && cd src \
    && tar -xvf zstd-${ZSTD_VERSION}.tar.gz \
    && cd zstd-${ZSTD_VERSION}/ \
    && make PREFIX=$ROOTDIR ZSTD_LEGACY_SUPPORT=0 \
    && make install PREFIX=$ROOTDIR ZSTD_LEGACY_SUPPORT=0 \
    && make clean \
    && cd $ROOTDIR && rm -Rf src/zstd*

# Download, compile and install minimal GDAL
RUN wget -q -O $ROOTDIR/src/gdal-${GDAL_VERSION}.tar.gz https://github.com/OSGeo/gdal/archive/${GDAL_VERSION}.tar.gz \
    && cd src \
    && tar -xvf gdal-${GDAL_VERSION}.tar.gz \
    && cd gdal-${GDAL_VERSION}/gdal \
    && ./configure \
      --with-python \
      --with-zstd=$ROOTDIR \
      --with-geos \
      --with-proj \
      --with-geotiff=internal \
      --with-libtiff=internal \
      --with-libz=internal \
      --with-liblzma=yes \
      --without-curl \
      --without-spatialite \
      --without-pg \
      --without-openjpeg \
      --without-bsb \
      --without-cfitsio \
      --without-cryptopp \
      --without-ecw \
      --without-expat \
      --without-fme \
      --without-freexl \
      --without-gif \
      --without-gif \
      --without-gnm \
      --without-grass \
      --without-grib \
      --without-hdf4 \
      --without-hdf5 \
      --without-idb \
      --without-ingres \
      --without-jasper \
      --without-jp2mrsid \
      --without-kakadu \
      --without-libgrass \
      --without-libkml \
      --without-mrf \
      --without-mrsid \
      --without-mysql \
      --without-netcdf \
      --without-odbc \
      --without-ogdi \
      --without-pcidsk \
      --without-pcraster \
      --without-pcre \
      --without-perl \
      --without-pg \
      --without-php \
      --without-png \
      --without-qhull \
      --without-sde \
      --without-xerces \
      --without-xml2 \
    && make && make install && ldconfig \
    && apt-get update -y \
    && cd $ROOTDIR && cd src/gdal-${GDAL_VERSION}/gdal/swig/python \
    && python3 setup.py build \
    && python3 setup.py install \
    && cd $ROOTDIR && rm -Rf src/gdal*

# Set up the benchmark script and sample files
ENV GTIFF_BENCHMARK_VERSION gdal-master

RUN wget -q -O $ROOTDIR/geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}.tar.gz https://github.com/kokoalberti/geotiff-benchmark/archive/${GTIFF_BENCHMARK_VERSION}.tar.gz \
  && tar -xvf geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}.tar.gz \
  && rm geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}.tar.gz

RUN wget -q -O $ROOTDIR/geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}/input_rasters/geotiff_sample_files.tar.gz https://s3.us-east-2.amazonaws.com/geotiff-benchmark-sample-files/geotiff_sample_files.tar.gz \
  && cd $ROOTDIR/geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}/input_rasters/ \
  && tar -xvf $ROOTDIR/geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}/input_rasters/geotiff_sample_files.tar.gz \
  && rm $ROOTDIR/geotiff-benchmark-${GTIFF_BENCHMARK_VERSION}/input_rasters/geotiff_sample_files.tar.gz

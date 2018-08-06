## Geotiff benchmark

Code for running benchmarks for different compression algorithms in GDAL's GeoTIFF driver. More information
on the benchmark and results in the related article on [my website](https://kokoalberti.com).

## Running your own benchmarks

You can run your own benchmarks using a prepared Docker environment, or just locally on your own computer.

### Local

To run the benchmark locally, add the GeoTIFF files you want to benchmark with to the `input_files` 
directory, and run the benchmark script:

    python3 geotiff_benchmark.py

A few notes:

* You may have to run the script as root, because it calls itself using `perf stat` to time the 
benchmarks.
* Make sure you have GDAL properly installed. To test `zstd` compression at least GDAL 2.4.0-dev is required.
* Modify the `config.ini` file to suit your needs. See the [GeoTIFF File Format](https://www.gdal.org/frmt_gtiff.html) for 
valid settings.
* Don't have any sample files? Download the demo files I used (50Mb files with different data types) from [here](https://s3.us-east-2.amazonaws.com/geotiff-benchmark-sample-files/geotiff_sample_files.tar.gz).
* Use ``--repetitions`` to set the number of repetitions, ``--input`` to define input directory with tif files, and ``--config`` to set the the correct config file.

### Using Docker

To run the benchmarks using Docker, use the included `Dockerfile` to build an image containing a lightweight 
GDAL 2.4.0dev with zstd compression compiled in. The `Makefile` contains some shortcuts to build the image:

    make build

Builds the docker image and tags it `geotiff-benchmark`. Use `make shell` to run the container and a get a shell,
`make test` to run a minimal benchmark using the settings in `config-minimal.ini`. To run the full benchmark in 
the container:

    make benchmark

A few notes:

* While building the Docker image the sample files are automatically downloaded.
* In order to get `perf stat` to work inside a container I needed to run the container with the `--privileged`
flag, so that's included in the `make benchmark` command as well.

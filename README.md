# Geotiff benchmark

Code for running benchmarks for different compression algorithms in GDAL's GeoTIFF driver. More information
on the benchmark and results in the related article on [my website](https://kokoalberti.com).

# Running your own benchmarks

To run the benchmarks yourself, use the included `Dockerfile` to build an image containing a lightweight 
GDAL 2.3.1 with zstd compression compiled in. The `Makefile` contains some shortcuts to build the image:

    `make build`

And run the benchmark in the container:

    `make benchmark`

You can add the file(s) you want to benchmark with to the `input_rasters` subdirectory. To configure the 
different GDAL options, modify the `config.ini` file to create new sections, each of which can contain
one or more GTiff creation options. See the [GeoTIFF File Format](https://www.gdal.org/frmt_gtiff.html) for 
valid settings.

# Notes

In order to get `perf stat` to work inside a container I needed to run the container with the `--privileged`
flag, so that's included in the `make benchmark` command as well.
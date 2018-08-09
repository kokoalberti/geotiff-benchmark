
SHELL = /bin/bash

build:
	docker build -f Dockerfile --tag geotiff-benchmark .

shell:
	docker run \
		--name geotiff-benchmark \
		--privileged \
		--volume $(shell pwd)/:/data \
		--rm \
		-it \
		geotiff-benchmark /bin/bash

test:
	docker run \
	    --name geotiff-benchmark \
	    --privileged \
	    --rm \
	    -it \
	    geotiff-benchmark /bin/bash -c "/usr/bin/python3 /usr/local/geotiff-benchmark-master/gtiff_benchmark.py --config /usr/local/geotiff-benchmark-master/config-minimal.ini --repetitions 1"

benchmark:
	docker run \
	    --name geotiff-benchmark \
	    --privileged \
	    --rm \
	    -it \
	    geotiff-benchmark /bin/bash -c "/usr/bin/python3 /usr/local/geotiff-benchmark-master/gtiff_benchmark.py --config /usr/local/geotiff-benchmark-master/config.ini --repetitions 10"

lerc:
	docker run \
	    --name geotiff-benchmark \
	    --privileged \
	    --rm \
	    -it \
	    geotiff-benchmark /bin/bash -c "/usr/bin/python3 /usr/local/geotiff-benchmark-master/gtiff_benchmark.py --config /usr/local/geotiff-benchmark-master/config-lerc.ini --repetitions 1"


clean:
	docker stop geotiff-benchmark
	docker rm geotiff-benchmark

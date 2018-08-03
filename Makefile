
SHELL = /bin/bash

build:
	docker build -f Dockerfile --tag geotiff-benchmark-master .

shell:
	docker run \
		--name geotiff-benchmark-master \
		--privileged \
		--volume $(shell pwd)/:/data \
		--rm \
		-it \
		geotiff-benchmark-master /bin/bash

benchmark:
	docker run \
	    --name geotiff-benchmark-master \
	    --privileged \
	    --rm \
	    -it \
	    geotiff-benchmark-master /bin/bash -c "/usr/bin/python3 /usr/local/geotiff-benchmark-master/gtiff_benchmark.py prepare && /usr/bin/python3 /usr/local/geotiff-benchmark-master/gtiff_benchmark.py run --config /usr/local/geotiff-benchmark-master/config.ini"

clean:
	docker stop geotiff-benchmark
	docker rm geotiff-benchmark

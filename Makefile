
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

benchmark:
	docker run \
	    --name geotiff-benchmark \
	    --privileged \
	    --rm \
	    --it \ 
	    geotiff-benchmark /usr/bin/python3 /usr/local/geotiff-benchmark-master/geotiff_benchmark.py prepare && /usr/bin/python3 /usr/local/geotiff-benchmark-master/geotiff_benchmark.py run

clean:
	docker stop geotiff-benchmark
	docker rm geotiff-benchmark

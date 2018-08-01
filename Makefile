
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
	#run the benchmark...

clean:
	docker stop geotiff-benchmark
	docker rm geotiff-benchmark

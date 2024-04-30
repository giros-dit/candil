# CANDIL
CANDIL (Context-Aware Network Data Integration Loom) is a semantic monitoring framework for integrating data from heterogeneous network sources. This work is a fork of a previous [open-source SDA repository](https://github.com/giros-dit/semantic-data-aggregator).

## Morph-KGC Guidelines

Build the image as follows:

```bash
cd morph-kgc
docker build -t morph-kgc --build-arg optional_dependencies="sqlite kafka" .
```

Then run the container like this:

```bash
cd ..
docker run -it -v ./mappings/containerlab/:/files morph-kgc-new /files/config.ini
```

## Acknowledgements

This work has been partly supported by project [ECTICS](https://www.dit.upm.es/~giros/project/ectics/) (PID2019-105257RB-C21), funded by:

![](docs/logos/MICIU_AEI_w400.jpg)

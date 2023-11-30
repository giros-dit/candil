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

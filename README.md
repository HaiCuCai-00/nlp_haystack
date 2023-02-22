# Usable

Start server:
```bash
python3 ./application.py
```

Start ElasticSearch and Apache Tika

```bash
docker run -d -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.0
docker run -d -p 9998:9998 apache/tika:latest
```

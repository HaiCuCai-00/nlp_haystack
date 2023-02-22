sudo docker run -d -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.0
sudo docker run -d -p 9998:9998 apache/tika:latest
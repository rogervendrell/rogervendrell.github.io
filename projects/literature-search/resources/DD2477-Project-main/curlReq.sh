#! /usr/bin/bash

curl -H "Content-type: multipart/form-data" \
	-F query="search with semantic context vectors" \
	-F semantic_search="True" \
	-F from_="0" \
	-X POST \
	http://localhost:5001/

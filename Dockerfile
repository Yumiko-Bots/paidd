FROM python:3.9.10

WORKDIR /app
COPY . /app
 
RUN pip install -r pip.txt
 
ENTRYPOINT ["python3"]
CMD python3 -m plugins

FROM python:3.6-slim
WORKDIR /app
COPY . .
RUN pip3 install discord.py
RUN pip3 install requests
RUN pip3 install json-rpc
CMD [ "python3", "./senko.py" ]

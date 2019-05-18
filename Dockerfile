FROM python:3.6-slim
ADD keywords.py /
ADD dice.py /
ADD cooldown.py /
ADD senko.py /
ADD keys.env /
RUN pip3 install discord.py
RUN pip3 install requests
RUN pip3 install json-rpc
CMD [ "python3", "./senko.py" ]

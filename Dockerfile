FROM python:3.6-slim
WORKDIR /app
COPY requirements.txt .
RUN python3 -m pip install --upgrade pip
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "python3", "-u", "senko.py" ]

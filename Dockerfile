FROM python:3.9.12
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN apt-get update
RUN apt install python3-dev build-essential --yes
RUN apt install libssl1.1 --yes
RUN apt install libssl-dev --yes
RUN apt-get install default-libmysqlclient-dev --yes
RUN apt-get install python3-tk --yes
RUN apt-get install manpages-dev --yes
RUN pip install -r requirements.txt
EXPOSE 80
#COPY main.py .
CMD python manage.py runserver 0.0.0.0:80
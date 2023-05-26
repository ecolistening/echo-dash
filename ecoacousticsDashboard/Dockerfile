FROM python:3.9
#LABEL authors="David Kadish"

ENV DASH_DEBUG_MODE True

WORKDIR /code

COPY requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app.py /code/app.py
COPY pages/* /code/pages/
COPY utils/* /code/utils/

EXPOSE 8050
CMD ["python", "app.py"]
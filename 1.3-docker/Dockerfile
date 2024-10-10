FROM python

WORKDIR /opt/stocks_products

COPY ./stocks_products .

RUN pip install -r requirements.txt
RUN python manage.py migrate

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
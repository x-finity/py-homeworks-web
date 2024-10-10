# Команды для запуска Docker

  

**Для nginx контейнера:**

`docker build -f .\Dockerfile_simple . --tag my_nginx`  
`docker run -d -p 8000:80 my_nginx`  

  

**Для Django контейнера:**

`docker build . --tag my_django_crud`  
`docker run -d -p 8000:8000 my_django_crud`  


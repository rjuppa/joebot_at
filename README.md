# joebot_at
Algorithmic Trader

install:
- docker-compose: `$ sudo apt install docker-compose`
- psql:           `$ sudo apt install postgresql-client-common`
- virtualenv:     `$ sudo apt install virtualenv`
- pip:            `$ sudo apt install python3-pip`

install python3:
`$ virtualenv -p python3 venv`
`$ pip3 install -r requirements/base.txt`

Set database using docker:
`$ docker-compose up -d`

`$ psql -h localhost -p 5555 -U pguser -d postgres -c "CREATE DATABASE joebo_at ENCODING = 'UTF8';"`

Test connection:
`$ psql -h localhost -p 5555 -U pguser -d joebo_at -W`

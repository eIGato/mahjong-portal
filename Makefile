COMPOSE_FILE=$(or $(COMPOSE_FILE_VAR), local.yml)

up:
	docker-compose -f $(COMPOSE_FILE) up

up_deamon:
	docker-compose -f $(COMPOSE_FILE) up -d

down:
	docker-compose -f $(COMPOSE_FILE) stop

logs:
	docker-compose -f $(COMPOSE_FILE) logs -f

shell:
	docker-compose -f $(COMPOSE_FILE) run --rm web bash

build_docker:
	docker-compose -f $(COMPOSE_FILE) build

test:
	docker-compose -f local.yml run --rm web python manage.py test --noinput

lint:
	pre-commit run --all-files

initial_data:
	docker-compose -f local.yml run --rm web python manage.py flush --noinput
	docker-compose -f local.yml run --rm web python manage.py migrate --noinput
	docker-compose -f local.yml run --rm web python manage.py initial_data

permissions:
	sudo chown -R $$USER:$$USER .

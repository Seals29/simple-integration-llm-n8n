DOCKER = docker
DOCKER_COMPOSE = $(DOCKER) compose
CONTAINER_OLLAMA = ollama
CONTAINER_WEBUI = open-webui

help:
	@echo "Available Targets:"
	@echo "  make start      - Menjalankan container (background)"
	@echo "  make stop       - Menghentikan dan menghapus container"
	@echo "  make restart    - Restart container"
	@echo "  make console-ollama - Masuk ke terminal Ollama"
	@echo "  make console-webui  - Masuk ke terminal WebUI"

start:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

view:
	$(DOCKER_COMPOSE) ps -a

console-ollama:
	$(DOCKER) exec -it $(CONTAINER_OLLAMA) /bin/sh

logs-ollama:
	$(DOCKER) logs -f $(CONTAINER_OLLAMA)

console-webui:
	$(DOCKER) exec -it $(CONTAINER_WEBUI) /bin/sh

logs-webui:
	$(DOCKER) logs -f $(CONTAINER_WEBUI)

.PHONY: help start stop restart console-ollama console-webui

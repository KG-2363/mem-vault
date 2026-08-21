.PHONY: dev seed lint test build push-all tf-init tf-plan tf-apply

# ── Local development ─────────────────────────────────────────────────────────

dev:
	docker compose up --build

dev-down:
	docker compose down -v

seed:
	python scripts/seed_data.py

# ── Linting & testing ─────────────────────────────────────────────────────────

lint:
	cd services/upload-service    && ruff check . && mypy .
	cd services/enhancement-service && ruff check . && mypy .
	cd services/delivery-service  && ruff check . && mypy .
	cd services/auth-service      && ruff check . && mypy .
	cd services/api-service       && ruff check . && mypy .
	cd portals/studio-portal      && npm run lint
	cd portals/institution-portal && npm run lint

test:
	cd services/upload-service    && pytest -q
	cd services/enhancement-service && pytest -q
	cd services/delivery-service  && pytest -q
	cd services/auth-service      && pytest -q
	cd services/api-service       && pytest -q

# ── Docker build & push ───────────────────────────────────────────────────────

IMAGE_REGISTRY ?= gcr.io/$(GCP_PROJECT_ID)
IMAGE_TAG      ?= latest

build:
	docker build -t $(IMAGE_REGISTRY)/upload-service:$(IMAGE_TAG)       services/upload-service
	docker build -t $(IMAGE_REGISTRY)/enhancement-service:$(IMAGE_TAG) services/enhancement-service
	docker build -t $(IMAGE_REGISTRY)/delivery-service:$(IMAGE_TAG)    services/delivery-service
	docker build -t $(IMAGE_REGISTRY)/auth-service:$(IMAGE_TAG)        services/auth-service
	docker build -t $(IMAGE_REGISTRY)/api-service:$(IMAGE_TAG)         services/api-service

push-all: build
	docker push $(IMAGE_REGISTRY)/upload-service:$(IMAGE_TAG)
	docker push $(IMAGE_REGISTRY)/enhancement-service:$(IMAGE_TAG)
	docker push $(IMAGE_REGISTRY)/delivery-service:$(IMAGE_TAG)
	docker push $(IMAGE_REGISTRY)/auth-service:$(IMAGE_TAG)
	docker push $(IMAGE_REGISTRY)/api-service:$(IMAGE_TAG)

# ── Terraform ─────────────────────────────────────────────────────────────────

TF_VARS ?= -var="project_id=$(GCP_PROJECT_ID)" -var="region=$(GCP_REGION)"

tf-init:
	cd terraform && terraform init

tf-plan:
	cd terraform && terraform plan $(TF_VARS)

tf-apply:
	cd terraform && terraform apply $(TF_VARS) -auto-approve

tf-destroy:
	cd terraform && terraform destroy $(TF_VARS)

# ── Portal ────────────────────────────────────────────────────────────────────

portal-install:
	cd portals/studio-portal      && npm ci
	cd portals/institution-portal && npm ci

portal-dev-studio:
	cd portals/studio-portal && npm run dev

portal-dev-institution:
	cd portals/institution-portal && npm run dev

portal-build:
	cd portals/studio-portal      && npm run build
	cd portals/institution-portal && npm run build

# ── dbt ──────────────────────────────────────────────────────────────────────

dbt-run:
	cd pipelines/dbt && dbt run --profiles-dir .

dbt-test:
	cd pipelines/dbt && dbt test --profiles-dir .

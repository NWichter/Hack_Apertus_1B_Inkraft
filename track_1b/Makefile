.PHONY: run test build

IMAGE ?= inkraft
MODE ?= replay
ENV_FILE := $(wildcard .env)

build:
	docker build -t $(IMAGE) .

# make run            recompute every result block from the stored responses and judgements (no keys, no GPU)
# make run MODE=full  query LLM_* (and judge with JUDGE_*), then score; LIMIT=50 for a smoke test
run: build
ifeq ($(MODE),full)
	docker run --rm $(if $(ENV_FILE),--env-file .env) \
		-e LLM_BASE_URL -e LLM_API_KEY -e LLM_NAME \
		-e JUDGE_BASE_URL -e JUDGE_API_KEY -e JUDGE_NAME \
		-e LIMIT -e CONDITIONS \
		-v "$(CURDIR)/data:/app/data" $(IMAGE) full
else
	docker run --rm $(IMAGE) replay
endif

test: build
	docker run --rm $(IMAGE) test

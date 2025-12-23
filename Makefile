PROJECT_NAME = numchuck
VERSION = 0.1.0

PLATFORM = $(shell uname)
CONFIG = Release
ROOT := $(PWD)
BUILD := $(ROOT)/build
SCRIPTS := $(ROOT)/scripts
THIRDPARTY = $(ROOT)/thirdparty
LIB = $(THIRDPARTY)/install/lib
CHUCK = $(THIRDPARTY)/install/bin/chuck
DIST = $(BUILD)/dist/$(PROJECT_NAME)
ARCH=$(shell uname -m)

# variants
BUNDLED=0
MULTI=0
UNIVERSAL=0

ifeq ($(PLATFORM), Darwin)
OS = "macos"
GENERATOR ?= "-GXcode"
ifeq ($(UNIVERSAL), 1)
DIST_NAME = $(PROJECT_NAME)-$(VERSION)-macos-universal
EXTRA_OPTIONS += -DCM_MACOS_UNIVERSAL=ON
endif
else
OS = "windows"
GENERATOR ?= ""
endif

DIST_NAME = $(PROJECT_NAME)-$(VERSION)-$(OS)-$(ARCH)
DMG = $(DIST_NAME).dmg
ZIP = $(DIST_NAME).zip


.PHONY: all build clean test install repl snap typecheck lint format

all: build

# build:
# 	@mkdir -p build && \
# 		cd build && \
# 		cmake $(GENERATOR) .. $(EXTRA_OPTIONS) && \
# 		cmake --build . --config '$(CONFIG)' && \
# 		cmake --install . --config '$(CONFIG)'

build:
	@uv sync --reinstall-package numchuck

clean:
	rm -rf build

test:
	@uv run pytest

repl:
	@uv run numchuck repl

snap:
	@git add --all . && git commit -m 'snap' && git push

typecheck:
	@uv run mypy src/

lint:
	@uv run ruff check --fix src/

format:
	@uv run ruff format src/



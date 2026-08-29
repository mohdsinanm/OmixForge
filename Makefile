APP_NAME = omixforge
VERSION ?= 1.2.0
ARCH = amd64
BUILD_DIR = $(APP_NAME)_$(VERSION)_$(ARCH)
ENTRY_POINT = src/__main__.py
BIN_NAME = $(APP_NAME)
DESKTOP_FILE = $(APP_NAME).desktop
ICON_NAME = $(APP_NAME).png
ICON_SOURCE = src/assets/$(ICON_NAME)
VERSION_SCRIPT = python3 scripts/sync_version.py

.PHONY: all clean build-deb build-bin sync-version release

all: remove-omix build-bin build-deb build-debian install-omix

sync-version:
	@$(VERSION_SCRIPT) "$(VERSION)"

release: sync-version
	@$(VERSION_SCRIPT) --release "Release $(VERSION)" "$(VERSION)"

build-bin: sync-version
	@echo "Building PyInstaller executable..."
	poetry run pyinstaller --name $(BIN_NAME) --onefile --noconsole $(ENTRY_POINT) --add-data "src/assets/omixforge.png:src/assets" --add-data "src/assets/users-alt.svg:src/assets" --add-data "src/assets/lock.svg:src/assets"
	@echo "Executable built at dist/$(BIN_NAME)"
	split -b 80M dist/omixforge dist/omixforge.part.


build-deb: sync-version
	@echo "Setting up package directory structure..."
	mkdir -p $(BUILD_DIR)/DEBIAN
	mkdir -p $(BUILD_DIR)/usr/bin
	mkdir -p $(BUILD_DIR)/usr/share/applications
	mkdir -p $(BUILD_DIR)/usr/share/icons

	@echo "Copying executable..."
	cp dist/$(BIN_NAME) $(BUILD_DIR)/usr/bin/$(APP_NAME)
	chmod +x $(BUILD_DIR)/usr/bin/$(APP_NAME)

	@echo "Copying desktop and icon files..."
	cp $(DESKTOP_FILE) $(BUILD_DIR)/usr/share/applications/
	cp $(ICON_SOURCE) $(BUILD_DIR)/usr/share/icons/

	@echo "Creating control file..."
	echo "Package: $(APP_NAME)" > $(BUILD_DIR)/DEBIAN/control
	echo "Version: $(VERSION)" >> $(BUILD_DIR)/DEBIAN/control
	echo "Section: science" >> $(BUILD_DIR)/DEBIAN/control
	echo "Priority: optional" >> $(BUILD_DIR)/DEBIAN/control
	echo "Architecture: $(ARCH)" >> $(BUILD_DIR)/DEBIAN/control
	echo "Depends: python3" >> $(BUILD_DIR)/DEBIAN/control
	echo "Maintainer: Sinan <mohamedysf@bicpu.edu.in>" >> $(BUILD_DIR)/DEBIAN/control
	echo "Description: OmixForge - offline bioinformatics workflow manager" >> $(BUILD_DIR)/DEBIAN/control
	echo " A desktop application for managing bioinformatics pipelines locally." >> $(BUILD_DIR)/DEBIAN/control

	@echo "All set! Run 'dpkg-deb --build $(BUILD_DIR)' to generate your .deb file."

build-debian: sync-version
	dpkg-deb --build $(BUILD_DIR)

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist __pycache__ *.spec $(BUILD_DIR) omixforge.png omixforge_*_amd64*.deb __main__.py
	find . -type d -name '__pycache__' -prune -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete

install-omix:
	sudo dpkg -i $(BUILD_DIR).deb

remove-omix:
	sudo apt remove omixforge --purge -y || true

dev: sync-version
	cp src/__main__.py __main__.py
	python3 __main__.py


configure:
	poetry install --no-root

test: configure
	QT_QPA_PLATFORM=offscreen poetry run pytest -q -k utils

test-all: configure
	QT_QPA_PLATFORM=offscreen poetry run pytest 
	
package: build-bin build-deb build-debian
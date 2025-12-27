APP_NAME = omixforge
VERSION = 1.0.0
ARCH = amd64
BUILD_DIR = $(APP_NAME)_$(VERSION)_$(ARCH)
ENTRY_POINT = src/__main__.py
BIN_NAME = $(APP_NAME)
DESKTOP_FILE = $(APP_NAME).desktop
ICON_NAME = $(APP_NAME).png

.PHONY: all clean build-deb build-bin

all: remove-omix build-bin build-deb build-debian install-omix

# Step 1: Build the PyInstaller executable
build-bin:
	@echo "Building PyInstaller executable..."
	pyinstaller --name $(BIN_NAME) --onefile --noconsole $(ENTRY_POINT) --add-data "src/assets/omixforge.png:src/assets" --add-data "src/assets/users-alt.svg:src/assets" --add-data "src/assets/lock.svg:src/assets"
	@echo "Executable built at dist/$(BIN_NAME)"

# Step 2: Prepare .deb package structure
build-deb:
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
	cp $(ICON_NAME) $(BUILD_DIR)/usr/share/icons/

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

build-debian:
	dpkg-deb --build $(BUILD_DIR)

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist __pycache__ *.spec $(BUILD_DIR)

install-omix:
	sudo dpkg -i $(BUILD_DIR).deb

remove-omix:
	sudo apt remove omixforge --purge -y || true

dev:
	cp src/__main__.py __main__.py
	python3 __main__.py

configure:
	poetry install --no-root

test: configure
	QT_QPA_PLATFORM=offscreen poetry run pytest -q -k utils

package: build-bin build-deb build-debian
# Local development targets
.PHONY: install-local local-droplet test-dev-droplet clean-local-droplets

install-local:
	pip install -e .

local-droplet:
	python3 -c "from letterhead_pdf.installer import create_applescript_droplet; create_applescript_droplet('$(HOME)/Stationery/easy.pdf', app_name='Local Test Droplet', output_dir='$(HOME)/Applications', local=True, python_path='$(shell which python3)')"

test-dev-droplet: test-files
	@echo "Creating development test droplet..."
	uv run python -m letterhead_pdf.main install $(TEST_LETTERHEAD) --dev --name "Test Dev Droplet" --output-dir $(HOME)/Desktop
	@echo "Development droplet created on Desktop"

clean-local-droplets:
	rm -rf $(HOME)/Applications/Local\ Test\ Droplet.app
	rm -rf $(HOME)/Desktop/Test\ Dev\ Droplet.app
# Makefile for Mac-letterhead

# Version management (single source of truth)
VERSION := 0.10.4

# Directory setup
TEST_DIR := tests
TEST_FILES_DIR := $(TEST_DIR)/files
TEST_UTILS_DIR := $(TEST_DIR)/utils
DIST_DIR := dist
BUILD_DIR := build
VENV_DIR := .venv

# Test files
TEST_LETTERHEAD := $(TEST_FILES_DIR)/test-letterhead.pdf
TEST_MD := $(TEST_FILES_DIR)/simple.md

# Python versions to test
PYTHON_VERSIONS := 3.11 

.PHONY: all clean test-all test-files test-deps publish $(addprefix test-py, $(PYTHON_VERSIONS))

# Create necessary directories
$(TEST_FILES_DIR):
	mkdir -p $(TEST_FILES_DIR)

# Test targets for each Python version (basic - PDF only)
define make-test-basic-target
test-py$(1)-basic: test-files
	@echo "Testing basic functionality (PDF only) with Python $(1)..."
	# Create venv and install basic dependencies
	uv venv --python $(1) $(VENV_DIR)-py$(1)-basic
	cd $(VENV_DIR)-py$(1)-basic && uv pip install -e ..
	# Version test
	cd $(VENV_DIR)-py$(1)-basic && uv run python -m letterhead_pdf.main --version > ../$(TEST_DIR)/version-py$(1)-basic.txt
	# Merge PDF test
	cd $(VENV_DIR)-py$(1)-basic && uv run python -m letterhead_pdf.main merge \
		../$(TEST_LETTERHEAD) \
		"Mac-letterhead-$(VERSION)-py$(1)-basic" \
		../$(TEST_FILES_DIR) \
		../$(TEST_FILES_DIR)/test-document.pdf \
		--output ../$(TEST_FILES_DIR)/Mac-letterhead-$(VERSION)-py$(1)-basic.pdf
endef

# Test targets for each Python version (full - PDF + Markdown)
define make-test-full-target
test-py$(1)-full: test-files
	@echo "Testing full functionality (PDF + Markdown) with Python $(1)..."
	# Create venv and install full dependencies
	uv venv --python $(1) $(VENV_DIR)-py$(1)-full --system-site-packages
	cd $(VENV_DIR)-py$(1)-full && uv pip install -e .. && uv pip install markdown && uv pip list | grep markdown && echo "import sys; sys.path.append('/Users/erik/Developer/GitHub/Mac-letterhead/$(VENV_DIR)-py$(1)-full/lib/python$(1)/site-packages'); print(sys.path); import markdown; print('Markdown imported successfully')" > test_import.py && uv run python test_import.py
	# Version test
	cd $(VENV_DIR)-py$(1)-full && uv run python -m letterhead_pdf.main --version > ../$(TEST_DIR)/version-py$(1)-full.txt
	# Merge Markdown test
	cd $(VENV_DIR)-py$(1)-full && PYTHONPATH=/Users/erik/Developer/GitHub/Mac-letterhead/$(VENV_DIR)-py$(1)-full/lib/python$(1)/site-packages:$$PYTHONPATH uv run python -m letterhead_pdf.main merge-md \
		../$(TEST_LETTERHEAD) \
		"Mac-letterhead-$(VERSION)-py$(1)-full" \
		../$(TEST_FILES_DIR) \
		../$(TEST_MD) \
		--output ../$(TEST_FILES_DIR)/Mac-letterhead-$(VERSION)-py$(1)-full.pdf
endef

$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-test-basic-target,$(ver))))
$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-test-full-target,$(ver))))

# Set up test files for specific Python version
define setup-test-files
	@echo "Setting up test files with Python $(1)..."
	# Create venv and install dependencies
	uv venv --python $(1)
	uv pip install -r $(TEST_UTILS_DIR)/requirements.txt
	# Generate test files
	cd $(TEST_UTILS_DIR) && uv run --python $(1) python create_letterhead.py
	cp README.md $(TEST_FILES_DIR)/test-document.md
	# Create a test PDF document for basic tests
	cd $(VENV_DIR) && uv pip install reportlab && uv run python -c "from reportlab.pdfgen import canvas; from reportlab.lib.pagesizes import letter; c = canvas.Canvas('../$(TEST_FILES_DIR)/test-document.pdf', pagesize=letter); c.setFont('Helvetica', 12); c.drawString(72, 700, 'Test Document'); c.drawString(72, 680, 'This is a test PDF document for Mac-letterhead testing.'); c.drawString(72, 660, 'The letterhead should be applied under this content.'); c.drawString(72, 640, 'Keep some headroom for the logo.'); c.save()"
endef

# Set up test files (uses first Python version in list)
test-files: $(TEST_FILES_DIR)
	$(call setup-test-files,$(word 1,$(PYTHON_VERSIONS)))

# Clean build artifacts and test files
clean:
	rm -rf $(DIST_DIR) $(BUILD_DIR) $(TEST_DIR)/*.pdf $(TEST_DIR)/*.txt $(VENV_DIR)*
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	cd $(TEST_UTILS_DIR) && make clean

# Update version in all necessary files
update-version:
	@echo "Updating version to $(VERSION)..."
	sed -i '' "s/^__version__ = .*/__version__ = \"$(VERSION)\"/" letterhead_pdf/__init__.py
	# Increment the revision in uv.lock to trigger dependency updates
	CURRENT_REVISION=$$(grep "^revision = " uv.lock | sed 's/revision = //'); \
	NEW_REVISION=$$((CURRENT_REVISION + 1)); \
	sed -i '' "s/^revision = .*/revision = $$NEW_REVISION/" uv.lock

# Run basic tests for all Python versions
test-basic: $(foreach ver,$(PYTHON_VERSIONS),test-py$(ver)-basic)
	@echo "All basic tests completed"

# Test targets for each Python version (full with WeasyPrint - PDF + Markdown with WeasyPrint)
# Note: WeasyPrint requires system dependencies to be installed:
#       brew install pango cairo fontconfig freetype harfbuzz
define make-test-full-weasyprint-target
test-py$(1)-full-weasyprint: test-files
	@echo "Testing full functionality with WeasyPrint (PDF + Markdown) with Python $(1)..."
	@echo "Note: This target requires system dependencies to be installed:"
	@echo "      brew install pango cairo fontconfig freetype harfbuzz"
	# Create venv and install full dependencies with WeasyPrint
	uv venv --python $(1) $(VENV_DIR)-py$(1)-full-weasyprint --system-site-packages
	cd $(VENV_DIR)-py$(1)-full-weasyprint && uv pip install -e ..[markdown] && uv pip list | grep markdown && uv pip list | grep weasyprint && echo "import sys; sys.path.append('/Users/erik/Developer/GitHub/Mac-letterhead/$(VENV_DIR)-py$(1)-full-weasyprint/lib/python$(1)/site-packages'); print(sys.path); import os; os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib:' + os.environ.get('DYLD_LIBRARY_PATH', ''); print('DYLD_LIBRARY_PATH:', os.environ.get('DYLD_LIBRARY_PATH')); import markdown; import weasyprint; print('Markdown and WeasyPrint imported successfully')" > test_import.py && DYLD_LIBRARY_PATH=/opt/homebrew/lib:$$DYLD_LIBRARY_PATH uv run python test_import.py
	# Version test
	cd $(VENV_DIR)-py$(1)-full-weasyprint && DYLD_LIBRARY_PATH=/opt/homebrew/lib:$$DYLD_LIBRARY_PATH uv run python -m letterhead_pdf.main --version > ../$(TEST_DIR)/version-py$(1)-full-weasyprint.txt
	# Merge Markdown test
	cd $(VENV_DIR)-py$(1)-full-weasyprint && PYTHONPATH=/Users/erik/Developer/GitHub/Mac-letterhead/$(VENV_DIR)-py$(1)-full-weasyprint/lib/python$(1)/site-packages:$$PYTHONPATH DYLD_LIBRARY_PATH=/opt/homebrew/lib:$$DYLD_LIBRARY_PATH uv run python -m letterhead_pdf.main merge-md \
		../$(TEST_LETTERHEAD) \
		"Mac-letterhead-$(VERSION)-py$(1)-full-weasyprint" \
		../$(TEST_FILES_DIR) \
		../$(TEST_MD) \
		--output ../$(TEST_FILES_DIR)/Mac-letterhead-$(VERSION)-py$(1)-full-weasyprint.pdf
endef

$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-test-full-weasyprint-target,$(ver))))

# Run full tests for all Python versions
test-full: $(foreach ver,$(PYTHON_VERSIONS),test-py$(ver)-full)
	@echo "All full tests completed"

# Run full tests with WeasyPrint for all Python versions
test-full-weasyprint: $(foreach ver,$(PYTHON_VERSIONS),test-py$(ver)-full-weasyprint)
	@echo "All full tests with WeasyPrint completed"

# Run all tests for all Python versions
test-all: test-basic test-full test-full-weasyprint
	@echo "All tests completed"

# Publish to GitHub and trigger PyPI release
publish: test-all
	@echo "Publishing version $(VERSION)..."
	# Ensure working directory is clean
	git diff-index --quiet HEAD || (echo "Working directory not clean" && exit 1)
	# Update version and commit
	$(MAKE) update-version
	git add letterhead_pdf/__init__.py uv.lock
	git commit -m "Release version $(VERSION)"
	git push origin main
	# Create and push tag
	git tag -a v$(VERSION) -m "Version $(VERSION)"
	git push origin v$(VERSION)
	@echo "Version $(VERSION) published and tagged. GitHub Actions will handle PyPI release."

# Show help
help:
	@echo "Available targets:"
	@echo "  test-all     - Run all tests with all Python versions ($(PYTHON_VERSIONS))"
	@echo "  test-basic   - Run basic tests (PDF only) with all Python versions"
	@echo "  test-full    - Run full tests (PDF + Markdown with ReportLab) with all Python versions"
	@echo "  test-full-weasyprint - Run full tests (PDF + Markdown with WeasyPrint) with all Python versions"
	@echo "  test-py<X>-basic - Test basic functionality with Python <X> (e.g., test-py3.11-basic)"
	@echo "  test-py<X>-full  - Test full functionality with Python <X> (e.g., test-py3.11-full)"
	@echo "  test-py<X>-full-weasyprint - Test full functionality with WeasyPrint with Python <X> (e.g., test-py3.11-full-weasyprint)"
	@echo "  test-dev-droplet - Create a development droplet using local code"
	@echo "  local-droplet - Create legacy local droplet (requires ~/Stationery/easy.pdf)"
	@echo "  clean-local-droplets - Remove development and local test droplets"
	@echo "  clean        - Remove build artifacts and test files"
	@echo "  test-files   - Set up test files in test directory"
	@echo "  publish      - Update version, push to GitHub, and trigger PyPI release"
	@echo "  help         - Show this help message"
	@echo ""
	@echo "Development workflow:"
	@echo "  1. make test-dev-droplet  # Create test droplet with local code"
	@echo "  2. Test the droplet by dragging files onto it"
	@echo "  3. make clean-local-droplets  # Clean up when done"
	@echo ""
	@echo "Current version: $(VERSION)"

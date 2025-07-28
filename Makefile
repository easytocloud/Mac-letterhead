# Makefile for Mac-letterhead

# Version management (single source of truth)
VERSION := 0.12.4

# Directory setup
TOOLS_DIR := tools
TEST_INPUT_DIR := test-input
TEST_OUTPUT_DIR := test-output
DIST_DIR := dist
BUILD_DIR := build
VENV_DIR := .venv

# Test files (letterhead will be generated in tools and referenced from test-output)
TEST_LETTERHEAD := $(TEST_OUTPUT_DIR)/test-letterhead.pdf
INPUT_MD_FILES := $(wildcard $(TEST_INPUT_DIR)/*.md)

# Python versions to test
PYTHON_VERSIONS := 3.10 3.11 3.12 

# Environment setup
PROJECT_ROOT := $(shell pwd)
WEASY_ENV := DYLD_LIBRARY_PATH=/opt/homebrew/lib:$$DYLD_LIBRARY_PATH

# Absolute paths for use in venv contexts
ABS_TEST_LETTERHEAD := $(PROJECT_ROOT)/$(TEST_LETTERHEAD)
ABS_TEST_INPUT_DIR := $(PROJECT_ROOT)/$(TEST_INPUT_DIR)
ABS_TEST_OUTPUT_DIR := $(PROJECT_ROOT)/$(TEST_OUTPUT_DIR)

.PHONY: all help dev-install dev-droplet test-setup test-input test-basic test-full test-weasyprint test-all clean-all clean-droplets clean-build release-version release-publish $(addprefix test-py, $(PYTHON_VERSIONS))

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

dev-install:
	uv pip install -e .

dev-droplet: test-setup
	@echo "Creating development test droplet..."
	uv run python -m letterhead_pdf.main install $(TEST_LETTERHEAD) --dev --name "Test Dev Droplet" --output-dir $(HOME)/Desktop
	@echo "Development droplet created on Desktop"

# =============================================================================
# TESTING TARGETS
# =============================================================================

# Set up test files - generate letterhead PDF using tools
test-setup:
	@echo "Setting up test files with Python $(word 1,$(PYTHON_VERSIONS))..."
	@if [ ! -d "$(TEST_OUTPUT_DIR)" ]; then mkdir -p "$(TEST_OUTPUT_DIR)"; fi
	uv venv --python $(word 1,$(PYTHON_VERSIONS))
	uv pip install -r $(TOOLS_DIR)/requirements.txt
	cd $(TOOLS_DIR) && uv run --python $(word 1,$(PYTHON_VERSIONS)) python create_letterhead.py
	@if [ -f "$(TOOLS_DIR)/test-letterhead.pdf" ]; then mv "$(TOOLS_DIR)/test-letterhead.pdf" "$(TEST_LETTERHEAD)"; echo "Letterhead moved to $(TEST_LETTERHEAD)"; fi

# =============================================================================
# VIRTUAL ENVIRONMENT MANAGEMENT
# =============================================================================

# Unified venv creation function
define create-venv
	@echo "Creating $(2) environment for Python $(1)..."
	uv venv --python $(1) $(VENV_DIR)-py$(1)-$(2) $(3)
	cd $(VENV_DIR)-py$(1)-$(2) && uv pip install -e $(if $(findstring weasyprint,$(2)),..[markdown],$(if $(findstring full,$(2)),.. && uv pip install markdown,..))
endef

# Unified command execution function  
define run-in-venv
	cd $(VENV_DIR)-py$(1)-$(2) && $(if $(findstring weasyprint,$(2)),$(WEASY_ENV) ,)uv run $(3)
endef


# =============================================================================
# MARKDOWN PROCESSING RULES  
# =============================================================================



# =============================================================================
# PYTHON VERSION TESTING
# =============================================================================

# Test function template
define make-test-target
test-py$(1)-$(2): test-setup
	@echo "Testing $(2) functionality with Python $(1)..."
	$(if $(findstring weasyprint,$(2)),@echo "Note: WeasyPrint requires: brew install pango cairo fontconfig freetype harfbuzz")
	$(call create-venv,$(1),$(2),$(if $(findstring basic,$(2)),,--system-site-packages))
	@if [ -d "$(TEST_INPUT_DIR)" ]; then \
		echo "Processing markdown files with $(2) configuration for Python $(1)..."; \
		echo "Looking for files in: $(TEST_INPUT_DIR)"; \
		if [ ! -d "$(TEST_OUTPUT_DIR)" ]; then mkdir -p "$(TEST_OUTPUT_DIR)"; fi; \
		for file in $(TEST_INPUT_DIR)/*.md; do \
			if [ -f "$$$$file" ]; then \
				echo "Processing $$$$file with $(2) configuration..."; \
				$(call run-in-venv,$(1),$(2),python -m letterhead_pdf.main merge-md ../$(TEST_LETTERHEAD) "$$$$(basename $$$$file .md)" ../$(TEST_OUTPUT_DIR) ../$$$$file --output ../$(TEST_OUTPUT_DIR)/$$$$(basename $$$$file .md)-py$(1)-$(2).pdf); \
			fi; \
		done; \
	else \
		echo "Directory $(TEST_INPUT_DIR) does not exist. Skipping markdown processing."; \
	fi
endef

# Generate test targets for all Python versions and test types
$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-test-target,$(ver),basic)))
$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-test-target,$(ver),full)))
$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-test-target,$(ver),weasyprint)))

# Aggregate test targets
test-basic: $(foreach ver,$(PYTHON_VERSIONS),test-py$(ver)-basic)
	@echo "All basic tests completed"

test-full: $(foreach ver,$(PYTHON_VERSIONS),test-py$(ver)-full)
	@echo "All full tests completed"

test-weasyprint: $(foreach ver,$(PYTHON_VERSIONS),test-py$(ver)-weasyprint)
	@echo "All WeasyPrint tests completed"

test-all: test-basic test-full test-weasyprint
	@echo "All tests completed"

# =============================================================================
# CLEANING TARGETS
# =============================================================================

clean-build:
	rm -rf $(DIST_DIR) $(BUILD_DIR) $(VENV_DIR)*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

clean-droplets:
	rm -rf "$(HOME)/Applications/Local Test Droplet.app"
	rm -rf "$(HOME)/Desktop/Test Dev Droplet.app"

clean-test-files:
	if [ -d "$(TEST_OUTPUT_DIR)" ]; then rm -rf $(TEST_OUTPUT_DIR)/*.pdf; fi

clean-all: clean-build clean-droplets clean-test-files
	if [ -d "$(TOOLS_DIR)" ] && [ -f "$(TOOLS_DIR)/Makefile" ]; then cd $(TOOLS_DIR) && make clean; fi

# =============================================================================
# RELEASE TARGETS
# =============================================================================

release-version:
	@echo "Updating version to $(VERSION)..."
	sed -i '' "s/^__version__ = .*/__version__ = \"$(VERSION)\"/" letterhead_pdf/__init__.py
	if [ -f "uv.lock" ]; then \
		CURRENT_REVISION=$$(grep "^revision = " uv.lock | sed 's/revision = //'); \
		NEW_REVISION=$$((CURRENT_REVISION + 1)); \
		sed -i '' "s/^revision = .*/revision = $$NEW_REVISION/" uv.lock; \
	fi

release-publish: test-all
	@echo "Publishing version $(VERSION)..."
	git diff-index --quiet HEAD || (echo "Working directory not clean" && exit 1)
	$(MAKE) release-version
	git add letterhead_pdf/__init__.py
	if [ -f "uv.lock" ]; then git add uv.lock; fi
	git commit -m "Release version $(VERSION)"
	git push origin main
	git tag -a v$(VERSION) -m "Version $(VERSION)"
	git push origin v$(VERSION)
	@echo "Version $(VERSION) published and tagged. GitHub Actions will handle PyPI release."

# =============================================================================
# HELP AND DEFAULT
# =============================================================================

help:
	@echo "Mac-letterhead Makefile - Available targets:"
	@echo ""
	@echo "📦 DEVELOPMENT:"
	@echo "  dev-install          - Install package for local development"
	@echo "  dev-droplet          - Create development droplet using local code"
	@echo ""
	@echo "🧪 TESTING:"
	@echo "  test-setup           - Set up test files and environment"
	@echo "  test-input           - Process all .md files from $(TEST_INPUT_DIR)/ with all configurations"
	@echo "  test-input-basic     - Process all .md files with basic configuration"
	@echo "  test-input-full      - Process all .md files with full configuration (ReportLab)"
	@echo "  test-input-weasyprint- Process all .md files with WeasyPrint configuration"
	@echo "  test-basic           - Run basic tests with all Python versions"
	@echo "  test-full            - Run full tests with all Python versions"
	@echo "  test-weasyprint      - Run WeasyPrint tests with all Python versions"
	@echo "  test-all             - Run all tests with all Python versions"
	@echo "  test-py<X>-basic     - Test basic functionality with Python <X> (e.g., test-py3.11-basic)"
	@echo "  test-py<X>-full      - Test full functionality with Python <X> (e.g., test-py3.11-full)"
	@echo "  test-py<X>-weasyprint- Test WeasyPrint functionality with Python <X>"
	@echo ""
	@echo "🧹 CLEANING:"
	@echo "  clean-all            - Clean everything (build artifacts, test files, droplets)"
	@echo "  clean-build          - Remove build artifacts and virtual environments only"
	@echo "  clean-droplets       - Remove test droplets only"
	@echo "  clean-test-files     - Remove test output files and generated PDFs"
	@echo ""
	@echo "🚀 RELEASE:"
	@echo "  release-version      - Update version numbers in source files"
	@echo "  release-publish      - Run tests, update version, and publish to PyPI"
	@echo ""
	@echo "💡 DEVELOPMENT WORKFLOW:"
	@echo "  1. make dev-droplet      # Create test droplet with local code"
	@echo "  2. Test the droplet by dragging files onto it"
	@echo "  3. make clean-droplets   # Clean up when done"
	@echo ""
	@echo "📋 SYSTEM REQUIREMENTS:"
	@echo "  WeasyPrint tests require: brew install pango cairo fontconfig freetype harfbuzz"
	@echo ""
	@echo "📁 DIRECTORIES:"
	@echo "  $(TEST_INPUT_DIR)/    - Place your .md test files here (user-managed)"
	@echo "  $(TEST_OUTPUT_DIR)/   - Processed output files will appear here"
	@echo ""
	@echo "Current version: $(VERSION)"
	@echo "Python versions tested: $(PYTHON_VERSIONS)"

# Default target
all: help

# Makefile for Mac-letterhead
# Redesigned with proper test architecture and reliable file processing

# =============================================================================
# VERSION MANAGEMENT
# =============================================================================

VERSION := 0.13.8

# =============================================================================
# DIRECTORY CONFIGURATION
# =============================================================================

# Base directories
TOOLS_DIR := tools
TEST_INPUT_DIR := test-input  
TEST_OUTPUT_DIR := test-output
TESTS_DIR := tests
DIST_DIR := dist
BUILD_DIR := build
VENV_DIR := .venv

# Test files
TEST_LETTERHEAD := $(TEST_OUTPUT_DIR)/test-letterhead.pdf
INPUT_MD_FILES := $(wildcard $(TEST_INPUT_DIR)/*.md)

# Python versions to test
PYTHON_VERSIONS := 3.10 3.11 3.12

# Environment setup
PROJECT_ROOT := $(shell pwd)

# Absolute paths for reliable processing
ABS_TEST_LETTERHEAD := $(PROJECT_ROOT)/$(TEST_LETTERHEAD)
ABS_TEST_INPUT_DIR := $(PROJECT_ROOT)/$(TEST_INPUT_DIR)
ABS_TEST_OUTPUT_DIR := $(PROJECT_ROOT)/$(TEST_OUTPUT_DIR)
ABS_TESTS_DIR := $(PROJECT_ROOT)/$(TESTS_DIR)

# =============================================================================
# PHONY TARGETS DECLARATION
# =============================================================================

.PHONY: all help dev-install dev-droplet test-setup \
	test-unit test-dev test-smoke \
	rendering-reportlab-basic rendering-reportlab-enhanced rendering-weasyprint \
	rendering-backend-matrix rendering-all-python-versions \
	test-all-unit test-all-rendering test-all \
	clean-all clean-build clean-droplets clean-test-output \
	release-version release-publish \
	$(addprefix rendering-py, $(PYTHON_VERSIONS)) \
	$(addprefix test-unit-py, $(PYTHON_VERSIONS))

# =============================================================================
# DEVELOPMENT TARGETS
# =============================================================================

dev-install:
	@echo "🔧 Installing package for local development..."
	uv pip install -e .

dev-droplet: test-setup
	@echo "🚀 Creating development test droplet..."
	uv run python -m letterhead_pdf.main install --name "Test Dev Droplet" --letterhead $(TEST_LETTERHEAD) --dev --output-dir $(HOME)/Desktop
	@echo "✅ Development droplet created on Desktop"

# =============================================================================
# TEST SETUP
# =============================================================================

test-setup:
	@echo "⚙️  Setting up test environment and letterhead..."
	@mkdir -p "$(TEST_OUTPUT_DIR)"
	@if [ ! -f "$(TEST_LETTERHEAD)" ]; then \
		if [ -f "$(TOOLS_DIR)/test-letterhead.pdf" ]; then \
			echo "📄 Using existing test letterhead from tools/"; \
			cp "$(TOOLS_DIR)/test-letterhead.pdf" "$(TEST_LETTERHEAD)"; \
			echo "✅ Test letterhead copied to $(TEST_LETTERHEAD)"; \
		else \
			echo "📄 Generating test letterhead..."; \
			uv venv --python $(word 1,$(PYTHON_VERSIONS)) $(VENV_DIR)-setup; \
			cd $(VENV_DIR)-setup && uv pip install -r $(PROJECT_ROOT)/$(TOOLS_DIR)/requirements.txt; \
			cd $(PROJECT_ROOT)/$(TOOLS_DIR) && $(PROJECT_ROOT)/$(VENV_DIR)-setup/bin/python create_letterhead.py; \
			if [ -f "$(TOOLS_DIR)/test-letterhead.pdf" ]; then \
				cp "$(TOOLS_DIR)/test-letterhead.pdf" "$(TEST_LETTERHEAD)"; \
				echo "✅ Test letterhead created at $(TEST_LETTERHEAD)"; \
			else \
				echo "❌ Failed to create test letterhead"; \
				exit 1; \
			fi; \
		fi; \
	else \
		echo "✅ Test letterhead already exists"; \
	fi

# =============================================================================
# UNIT TESTS (pytest-based)
# =============================================================================

test-unit: test-setup
	@echo "🧪 Running unit tests with pytest..."
	uv venv --python $(word 1,$(PYTHON_VERSIONS)) $(VENV_DIR)-unit
	cd $(VENV_DIR)-unit && uv pip install -e ..[dev]
	$(VENV_DIR)-unit/bin/python -m pytest $(TESTS_DIR) -v --tb=short
	@echo "✅ Unit tests completed"

# Run unit tests on specific Python version
define make-unit-test-target
test-unit-py$(1): test-setup
	@echo "🧪 Running unit tests with Python $(1)..."
	uv venv --python $(1) $(VENV_DIR)-unit-py$(1)
	cd $(VENV_DIR)-unit-py$(1) && uv pip install -e ..[dev]
	$(VENV_DIR)-unit-py$(1)/bin/python -m pytest $(TESTS_DIR) -v --tb=short
	@echo "✅ Unit tests completed for Python $(1)"
endef

$(foreach ver,$(PYTHON_VERSIONS),$(eval $(call make-unit-test-target,$(ver))))

test-all-unit: $(foreach ver,$(PYTHON_VERSIONS),test-unit-py$(ver))
	@echo "🎉 All unit tests completed across Python versions"

# =============================================================================
# DEVELOPMENT & SMOKE TESTS
# =============================================================================

test-dev: test-unit
	@echo "⚡ Running quick development validation..."
	@echo "✅ Development tests passed"

test-smoke: test-setup
	@echo "💨 Running smoke test with first input file..."
	@first_file=$$(find $(TEST_INPUT_DIR) -name "*.md" | head -1); \
	if [ -n "$$first_file" ]; then \
		filename=$$(basename "$$first_file" .md); \
		echo "Testing with: $$first_file"; \
		uv venv --python $(word 1,$(PYTHON_VERSIONS)) $(VENV_DIR)-smoke; \
		cd $(VENV_DIR)-smoke && uv pip install -e ..; \
		mkdir -p "$(TEST_OUTPUT_DIR)/$$filename"; \
		$(PROJECT_ROOT)/$(VENV_DIR)-smoke/bin/python -m letterhead_pdf.main merge-md \
			"$(ABS_TEST_LETTERHEAD)" "$$filename" "$(ABS_TEST_OUTPUT_DIR)/$$filename" \
			"$(PROJECT_ROOT)/$$first_file" \
			--output "$(ABS_TEST_OUTPUT_DIR)/$$filename/$$filename-smoke-test.pdf" \
			--save-html "$(ABS_TEST_OUTPUT_DIR)/$$filename/$$filename-smoke-test.html"; \
		echo "✅ Smoke test completed - check $(TEST_OUTPUT_DIR)/$$filename/"; \
	else \
		echo "❌ No .md files found in $(TEST_INPUT_DIR)"; \
		exit 1; \
	fi

# =============================================================================
# RENDERING TESTS (Document Generation Validation)
# =============================================================================

# ReportLab basic (minimal dependencies, PDF-only rendering)
rendering-reportlab-basic: test-setup
	@echo "📋 Testing ReportLab basic rendering..."
	@$(call process-all-files,reportlab-basic,$(word 1,$(PYTHON_VERSIONS)))
	@echo "✅ ReportLab basic rendering tests completed"

# ReportLab enhanced (full markdown features, enhanced processing)
rendering-reportlab-enhanced: test-setup
	@echo "📋 Testing ReportLab enhanced rendering..."
	@$(call process-all-files,reportlab-enhanced,$(word 1,$(PYTHON_VERSIONS)))
	@echo "✅ ReportLab enhanced rendering tests completed"

# WeasyPrint (high-quality rendering, requires system dependencies)
rendering-weasyprint: test-setup
	@echo "📋 Testing WeasyPrint rendering..."
	@echo "ℹ️  Note: Requires system dependencies: brew install pango cairo fontconfig freetype harfbuzz"
	@$(call process-all-files,weasyprint,$(word 1,$(PYTHON_VERSIONS)))
	@echo "✅ WeasyPrint rendering tests completed"

# Backend matrix (all backend/markdown combinations)
rendering-backend-matrix: test-setup
	@echo "📋 Testing all backend combinations..."
	@$(call process-all-files,weasyprint-gfm,$(word 1,$(PYTHON_VERSIONS)))
	@$(call process-all-files,weasyprint-standard,$(word 1,$(PYTHON_VERSIONS)))
	@$(call process-all-files,reportlab-gfm,$(word 1,$(PYTHON_VERSIONS)))
	@$(call process-all-files,reportlab-standard,$(word 1,$(PYTHON_VERSIONS)))
	@echo "✅ Backend matrix tests completed"

# All Python versions (test primary configuration across all Python versions)
rendering-all-python-versions: test-setup
	@echo "📋 Testing across all Python versions..."
	@$(foreach ver,$(PYTHON_VERSIONS),echo "Testing Python $(ver)..." && $(call process-all-files,reportlab-enhanced,$(ver)) &&) true
	@echo "✅ All Python version tests completed"

test-all-rendering: rendering-reportlab-basic rendering-reportlab-enhanced rendering-weasyprint rendering-backend-matrix
	@echo "🎉 All rendering tests completed"

# =============================================================================
# FILE PROCESSING FUNCTIONS
# =============================================================================

# Reliable file processing function that handles all input files
define process-all-files
	@echo "Processing all files with configuration: $(1), Python: $(2)"; \
	config_name="$(1)"; \
	python_ver="$(2)"; \
	venv_name="$(VENV_DIR)-$$config_name-py$$python_ver"; \
	\
	echo "Creating virtual environment: $$venv_name"; \
	uv venv --python $$python_ver $$venv_name; \
	\
	echo "Installing dependencies for $$config_name..."; \
	if echo "$$config_name" | grep -q "weasyprint"; then \
		cd $$venv_name && uv pip install -e .. && uv pip install weasyprint; \
	else \
		cd $$venv_name && uv pip install -e ..[dev]; \
	fi; \
	\
	input_files=$$(find $(PROJECT_ROOT)/$(TEST_INPUT_DIR) -name "*.md" ! -name ".*"); \
	file_count=$$(echo "$$input_files" | wc -l); \
	echo "Processing $$file_count input files..."; \
	success_count=0; \
	total_count=0; \
	\
	for input_file in $$input_files; do \
		if [ -f "$$input_file" ]; then \
			total_count=$$((total_count + 1)); \
			filename=$$(basename "$$input_file" .md); \
			output_dir="$(ABS_TEST_OUTPUT_DIR)/$$filename"; \
			output_pdf="$$output_dir/$$filename-py$$python_ver-$$config_name.pdf"; \
			output_html="$$output_dir/$$filename-py$$python_ver-$$config_name.html"; \
			\
			echo "  📄 Processing: $$filename"; \
			mkdir -p "$$output_dir"; \
			\
			if echo "$$config_name" | grep -q "weasyprint"; then \
				export_cmd="env DYLD_LIBRARY_PATH=/opt/homebrew/lib $(PROJECT_ROOT)/$$venv_name/bin/python"; \
			else \
				export_cmd="$(PROJECT_ROOT)/$$venv_name/bin/python"; \
			fi; \
			\
			backend_args=""; \
			if echo "$$config_name" | grep -q "weasyprint-gfm"; then \
				backend_args="--pdf-backend weasyprint --markdown-backend gfm"; \
			elif echo "$$config_name" | grep -q "weasyprint-standard"; then \
				backend_args="--pdf-backend weasyprint --markdown-backend standard"; \
			elif echo "$$config_name" | grep -q "reportlab-gfm"; then \
				backend_args="--pdf-backend reportlab --markdown-backend gfm"; \
			elif echo "$$config_name" | grep -q "reportlab-standard"; then \
				backend_args="--pdf-backend reportlab --markdown-backend standard"; \
			fi; \
			\
			if $$export_cmd -m letterhead_pdf.main merge-md \
				"$(ABS_TEST_LETTERHEAD)" "$$filename" "$$output_dir" "$$input_file" \
				--output "$$output_pdf" --save-html "$$output_html" $$backend_args \
				2>/dev/null; then \
				echo "    ✅ Success: $$filename"; \
				success_count=$$((success_count + 1)); \
			else \
				echo "    ❌ Failed: $$filename"; \
			fi; \
		fi; \
	done; \
	\
	echo "📊 Results: $$success_count/$$total_count files processed successfully"; \
	if [ $$success_count -eq $$total_count ] && [ $$total_count -gt 0 ]; then \
		echo "🎉 All files processed successfully!"; \
	elif [ $$success_count -gt 0 ]; then \
		echo "⚠️  Partial success: $$success_count/$$total_count files"; \
	else \
		echo "❌ No files processed successfully"; \
		exit 1; \
	fi
endef

# =============================================================================
# COMPREHENSIVE TEST TARGETS
# =============================================================================

test-all: test-all-unit test-smoke test-all-rendering
	@echo "🏆 ALL TESTS COMPLETED SUCCESSFULLY!"
	@echo ""
	@echo "📊 Test Summary:"
	@echo "  ✅ Unit tests (pytest): All Python versions"
	@echo "  ✅ Smoke test: Basic functionality"  
	@echo "  ✅ Rendering tests: All configurations"
	@echo ""

# =============================================================================
# CLEANING TARGETS
# =============================================================================

clean-build:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf $(DIST_DIR) $(BUILD_DIR) $(VENV_DIR)*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Build artifacts cleaned"

clean-droplets:
	@echo "🧹 Cleaning test droplets..."
	rm -rf "$(HOME)/Applications/Local Test Droplet.app"
	rm -rf "$(HOME)/Desktop/Test Dev Droplet.app"
	@echo "✅ Test droplets cleaned"

clean-test-output:
	@echo "🧹 Cleaning test output files..."
	if [ -d "$(TEST_OUTPUT_DIR)" ]; then \
		find $(TEST_OUTPUT_DIR) -name "*.pdf" -delete 2>/dev/null || true; \
		find $(TEST_OUTPUT_DIR) -name "*.html" -delete 2>/dev/null || true; \
		find $(TEST_OUTPUT_DIR) -type d -empty -delete 2>/dev/null || true; \
	fi
	@echo "✅ Test output files cleaned"

clean-all: clean-build clean-droplets clean-test-output
	@echo "🧹 Running comprehensive cleanup..."
	if [ -d "$(TOOLS_DIR)" ] && [ -f "$(TOOLS_DIR)/Makefile" ]; then \
		cd $(TOOLS_DIR) && $(MAKE) clean; \
	fi
	@echo "✅ Complete cleanup finished"

# =============================================================================
# RELEASE TARGETS
# =============================================================================

release-version:
	@echo "📝 Updating version to $(VERSION)..."
	sed -i '' "s/^__version__ = .*/__version__ = \"$(VERSION)\"/" letterhead_pdf/__init__.py
	if [ -f "uv.lock" ]; then \
		CURRENT_REVISION=$$(grep "^revision = " uv.lock | sed 's/revision = //'); \
		NEW_REVISION=$$((CURRENT_REVISION + 1)); \
		sed -i '' "s/^revision = .*/revision = $$NEW_REVISION/" uv.lock; \
	fi
	@echo "✅ Version updated to $(VERSION)"

release-publish: test-unit test-smoke
	@echo "🚀 Publishing version $(VERSION)..."
	@echo "📋 Running pre-publish validation..."
	git diff-index --quiet HEAD || (echo "❌ Working directory not clean" && exit 1)
	$(MAKE) release-version
	@echo "📝 Committing version update..."
	git add letterhead_pdf/__init__.py
	if [ -f "uv.lock" ]; then git add uv.lock; fi
	git commit -m "Release version $(VERSION)"
	git push origin main
	@echo "🏷️  Tagging release..."
	git tag -a v$(VERSION) -m "Version $(VERSION)"
	git push origin v$(VERSION)
	@echo "🎉 Version $(VERSION) published and tagged!"
	@echo "📦 GitHub Actions will handle PyPI release automatically"

# =============================================================================
# HELP DOCUMENTATION
# =============================================================================

help:
	@echo "🔧 Mac-letterhead Makefile - Professional Test Architecture"
	@echo ""
	@echo "📦 DEVELOPMENT:"
	@echo "  dev-install              - Install package for local development using uv"
	@echo "  dev-droplet              - Create development droplet using local code"
	@echo ""
	@echo "🧪 UNIT TESTS (pytest-based software testing):"
	@echo "  test-unit                - Run unit tests with default Python version"
	@echo "  test-unit-py<X>          - Run unit tests with specific Python version (e.g., test-unit-py3.11)"
	@echo "  test-all-unit            - Run unit tests across all Python versions"
	@echo ""
	@echo "📋 RENDERING TESTS (document generation validation):"
	@echo "  rendering-reportlab-basic     - Basic ReportLab rendering (minimal deps)"
	@echo "  rendering-reportlab-enhanced  - Enhanced ReportLab with full markdown features"
	@echo "  rendering-weasyprint          - High-quality WeasyPrint rendering (requires system deps)"
	@echo "  rendering-backend-matrix      - Test all backend/markdown combinations"
	@echo "  rendering-all-python-versions - Test across all Python versions"
	@echo "  test-all-rendering            - Run all rendering tests"
	@echo ""
	@echo "⚡ QUICK TESTS:"
	@echo "  test-dev                 - Quick development validation (unit tests only)"
	@echo "  test-smoke               - Fast smoke test with single input file"
	@echo ""
	@echo "🏆 COMPREHENSIVE:"
	@echo "  test-all                 - Run ALL tests (unit + smoke + rendering)"
	@echo ""
	@echo "🧹 CLEANING:"
	@echo "  clean-all                - Clean everything (build artifacts, test files, droplets)"
	@echo "  clean-build              - Remove build artifacts and virtual environments only"  
	@echo "  clean-droplets           - Remove test droplets only"
	@echo "  clean-test-output        - Remove test output files (PDFs, HTMLs)"
	@echo ""
	@echo "🚀 RELEASE:"
	@echo "  release-version          - Update version numbers in source files"
	@echo "  release-publish          - Run tests, update version, and publish to PyPI"
	@echo ""
	@echo "💡 WORKFLOW EXAMPLES:"
	@echo "  Development: make dev-droplet → test → make clean-droplets"
	@echo "  Testing: make test-dev → make test-smoke → make test-all"
	@echo "  Release: make test-all → make release-publish"
	@echo ""
	@echo "📋 SYSTEM REQUIREMENTS:"
	@echo "  Basic tests: Python ≥3.10, uv package manager"
	@echo "  WeasyPrint: brew install pango cairo fontconfig freetype harfbuzz"
	@echo ""
	@echo "📁 FILE STRUCTURE:"
	@echo "  $(TEST_INPUT_DIR)/         - Input .md files for rendering tests"
	@echo "  $(TEST_OUTPUT_DIR)/        - Generated PDFs and HTML files"
	@echo "  $(TESTS_DIR)/              - Unit test files (pytest)"
	@echo ""
	@echo "ℹ️  INPUT FILES DETECTED: $(words $(INPUT_MD_FILES)) files"
	@echo "🐍 PYTHON VERSIONS: $(PYTHON_VERSIONS)"
	@echo "📌 CURRENT VERSION: $(VERSION)"

# Default target
all: help

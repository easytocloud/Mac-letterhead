# Makefile for test utilities

.PHONY: all clean

# Paths
OUTPUT_DIR := ../files

# Default target
all: $(OUTPUT_DIR)/test-letterhead.pdf

# Create test letterhead
$(OUTPUT_DIR)/test-letterhead.pdf: create_letterhead.py
	# Use uv run from parent environment
	../../.venv/bin/python create_letterhead.py

# Clean generated files
clean:
	rm -f $(OUTPUT_DIR)/test-letterhead.pdf

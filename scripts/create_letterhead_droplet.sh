#!/bin/bash
# Script to create an AppleScript Droplet application for Mac-letterhead

set -e

# Ensure we're in the scripts directory
cd "$(dirname "$0")"

# Default paths
APP_NAME="Letterhead Applier.app"
APP_DIR="$HOME/Desktop/$APP_NAME"
APPLESCRIPT_SRC="letterhead_fixed.applescript"
# Use a built-in macOS icon
ICON_PATH="/System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/GenericDocumentIcon.icns"

# Help text
show_help() {
    echo "Usage: $0 [options] /path/to/letterhead.pdf"
    echo ""
    echo "Options:"
    echo "  -o, --output DIR   Specify output directory (default: Desktop)"
    echo "  -n, --name NAME    Specify app name (default: 'Letterhead Applier')"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 ~/Documents/company_letterhead.pdf"
    echo "  $0 --name 'Company Letterhead' ~/Documents/company_letterhead.pdf"
    exit 1
}

# Process options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -n|--name)
            CUSTOM_NAME="$2"
            APP_NAME="${CUSTOM_NAME}.app"
            APP_DIR="$HOME/Desktop/$APP_NAME"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            LETTERHEAD_PATH="$1"
            shift
            ;;
    esac
done

# Check if the letterhead path was provided
if [ -z "$LETTERHEAD_PATH" ]; then
    echo "Error: You must specify a letterhead PDF file."
    show_help
fi

# Check if the letterhead file exists
if [ ! -f "$LETTERHEAD_PATH" ]; then
    echo "Error: Letterhead file '$LETTERHEAD_PATH' not found."
    exit 1
fi

# Check if we have osascript (AppleScript compiler)
if ! command -v osacompile &> /dev/null; then
    echo "Error: osacompile not found. This script requires macOS."
    exit 1
fi

# Create a temporary directory
TMP_DIR=$(mktemp -d)
RESOURCES_DIR="$TMP_DIR/Resources"
mkdir -p "$RESOURCES_DIR"

# If the output directory was specified, use it
if [ -n "$OUTPUT_DIR" ]; then
    APP_DIR="$OUTPUT_DIR/$APP_NAME"
fi

echo "Creating AppleScript Droplet application..."
echo "  Letterhead: $LETTERHEAD_PATH"
echo "  App will be saved to: $APP_DIR"

# Copy the letterhead to the resources directory
cp "$LETTERHEAD_PATH" "$RESOURCES_DIR/letterhead.pdf"
echo "✅ Copied letterhead to resources"

# Compile the AppleScript to an application
osacompile -o "$APP_DIR" "$APPLESCRIPT_SRC"
if [ $? -ne 0 ]; then
    echo "❌ Failed to compile AppleScript."
    exit 1
fi
echo "✅ Compiled AppleScript application"

# Clean up the temporary directory
FINAL_RESOURCES_DIR="$APP_DIR/Contents/Resources"
mkdir -p "$FINAL_RESOURCES_DIR"
cp "$RESOURCES_DIR/letterhead.pdf" "$FINAL_RESOURCES_DIR/"
echo "✅ Added letterhead to app bundle"

# Set the icon if it exists
if [ -f "$ICON_PATH" ]; then
    # If it's already an .icns file, copy it directly
    if [[ "$ICON_PATH" == *.icns ]]; then
        cp "$ICON_PATH" "$APP_DIR/Contents/Resources/applet.icns"
        echo "✅ Set custom icon"
    # Otherwise try to convert it using sips if available
    elif command -v sips &> /dev/null && [[ "$ICON_PATH" == *.png ]]; then
        # Create iconset with multiple sizes
        ICON_BASE=$(basename "$ICON_PATH" .png)
        ICONSET_DIR="$TMP_DIR/${ICON_BASE}.iconset"
        mkdir -p "$ICONSET_DIR"
        
        for size in 16 32 64 128 256 512; do
            sips -z $size $size "$ICON_PATH" --out "${ICONSET_DIR}/icon_${size}x${size}.png" > /dev/null 2>&1
            sips -z $((size*2)) $((size*2)) "$ICON_PATH" --out "${ICONSET_DIR}/icon_${size}x${size}@2x.png" > /dev/null 2>&1
        done
        
        # Convert iconset to icns
        if command -v iconutil &> /dev/null; then
            iconutil -c icns -o "$TMP_DIR/${ICON_BASE}.icns" "$ICONSET_DIR"
            cp "$TMP_DIR/${ICON_BASE}.icns" "$APP_DIR/Contents/Resources/applet.icns"
            echo "✅ Set custom icon"
        fi
    fi
fi

# Clean up
rm -rf "$TMP_DIR"

echo ""
echo "✅ Letterhead Droplet application successfully created!"
echo ""
echo "You can now:"
echo "1. Drag and drop PDF files onto the application icon"
echo "2. The letterhead will be applied automatically"
echo "3. You'll be prompted to save the merged document"
echo ""
echo "The application is located at: $APP_DIR"

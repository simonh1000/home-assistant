#!/bin/bash

# Configuration
OUTPUT_FILE="automations.yaml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
SMB_TARGET="//192.168.0.183/config"

# Parse arguments
DEPLOY=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --deploy) DEPLOY=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Load environment variables for deployment if needed
if [ "$DEPLOY" = true ]; then
    if [ -f "$SCRIPT_DIR/.env" ]; then
        export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
    else
        echo "Error: .env file not found. Required for deployment."
        exit 1
    fi
    
    if [ -z "$HA_USER" ] || [ -z "$HA_PASSWORD" ]; then
        echo "Error: HA_USER or HA_PASSWORD not set in .env."
        exit 1
    fi
fi

# Single source of truth for which files get combined.
# Automatically finds all .yaml files in the current directory (excluding the output file itself).
YAML_FILES=()
while IFS=  read -r -d '' file; do
    filename=$(basename "$file")
    if [ "$filename" != "$OUTPUT_FILE" ]; then
        YAML_FILES+=("$filename")
    fi
done < <(find . -maxdepth 1 -name "*.yaml" -print0 | sort -z)

SOURCE_FILE_LIST=$(IFS=, ; echo "${YAML_FILES[*]}")

# Header for the consolidated file
cat << EOF > "$SCRIPT_DIR/$OUTPUT_FILE"
###############################################################################
# AUTO-GENERATED MASTER AUTOMATIONS FILE - DO NOT EDIT MANUALLY
# Generated on: $TIMESTAMP
# Source files: $SOURCE_FILE_LIST
#
# To update this file:
# 1. Edit the individual .yaml files in this directory.
# 2. Run this script: ./combine.sh
###############################################################################

EOF

# Function to add a file to the master list
add_to_master() {
    local file=$1
    # Generate ID from filename: remove .yaml and replace - with _
    local id=$(echo "$file" | sed 's/\.yaml$//; s/-/_/g')

    if [ -f "$SCRIPT_DIR/$file" ]; then
        echo "# --- Source: $file ---" >> "$SCRIPT_DIR/$OUTPUT_FILE"
        # Add the list marker and the ID
        echo "- id: $id" >> "$SCRIPT_DIR/$OUTPUT_FILE"
        # Indent the original file content and append
        sed 's/^/  /' "$SCRIPT_DIR/$file" >> "$SCRIPT_DIR/$OUTPUT_FILE"
        echo "" >> "$SCRIPT_DIR/$OUTPUT_FILE"
        echo "Added $file with id $id"
    else
        echo "Warning: $file not found, skipping."
    fi
}

for file in "${YAML_FILES[@]}"; do
    add_to_master "$file"
done

# Validate the result is well-formed YAML before handing it to Home Assistant
if command -v python3 >/dev/null 2>&1; then
    yaml_error=$(mktemp)
    if ! python3 -c "import sys, yaml; yaml.safe_load(open(sys.argv[1]))" "$SCRIPT_DIR/$OUTPUT_FILE" 2>"$yaml_error"; then
        echo "ERROR: Generated $OUTPUT_FILE is not valid YAML:"
        cat "$yaml_error"
        rm -f "$yaml_error"
        exit 1
    fi
    rm -f "$yaml_error"
else
    echo "Warning: python3 not found, skipping YAML validation."
fi

echo "Done! Consolidated file created at $SCRIPT_DIR/$OUTPUT_FILE"

# Deployment step
if [ "$DEPLOY" = true ]; then
    echo "Deploying to Home Assistant..."
    
    # Check if already mounted (common on macOS with Finder/Samba)
    EXISTING_MOUNT=$(mount | grep "//${HA_USER}@192.168.0.183/config" | awk '{print $3}')
    
    if [ -n "$EXISTING_MOUNT" ] && [ -d "$EXISTING_MOUNT" ]; then
        echo "Found existing mount at $EXISTING_MOUNT. Copying..."
        cp "$SCRIPT_DIR/$OUTPUT_FILE" "$EXISTING_MOUNT/"
        if [ $? -eq 0 ]; then
            echo "Successfully deployed $OUTPUT_FILE to $EXISTING_MOUNT"
        else
            echo "Failed to copy to existing mount."
            exit 1
        fi
    elif command -v smbclient >/dev/null 2>&1; then
        echo "Using smbclient to deploy..."
        smbclient "$SMB_TARGET" -U "$HA_USER%$HA_PASSWORD" -c "put $OUTPUT_FILE"
        if [ $? -eq 0 ]; then
            echo "Successfully deployed $OUTPUT_FILE to $SMB_TARGET"
        else
            echo "Failed to deploy via smbclient."
            exit 1
        fi
    else
        # Fallback to mount (macOS style)
        echo "Attempting to mount $SMB_TARGET..."
        MOUNT_POINT=$(mktemp -d)
        mount_smbfs "//$HA_USER:$HA_PASSWORD@192.168.0.183/config" "$MOUNT_POINT"
        if [ $? -eq 0 ]; then
            cp "$SCRIPT_DIR/$OUTPUT_FILE" "$MOUNT_POINT/"
            umount "$MOUNT_POINT"
            rmdir "$MOUNT_POINT"
            echo "Successfully deployed $OUTPUT_FILE to $SMB_TARGET"
        else
            echo "Error: smbclient not found and mount_smbfs failed (it might already be mounted elsewhere)."
            rmdir "$MOUNT_POINT"
            exit 1
        fi
    fi
fi

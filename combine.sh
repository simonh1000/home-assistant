#!/bin/bash

# Configuration
OUTPUT_FILE="automations.yaml"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Single source of truth for which files get combined, and under what id.
# Add new automations here only - the header and the build loop both read from this.
SOURCES=(
    "kitchen.yaml:energy_kitchen_guard"
    "ev-lockout.yaml:energy_ev_lockout"
    "ev-safety.yaml:energy_ev_safety_breaker"
    "ev-deadline-activate.yaml:energy_ev_deadline_activate"
    "ev-deadline-guard.yaml:energy_ev_deadline_guard"
    "ev-deadline-revert.yaml:energy_ev_deadline_revert"
    "test-notify.yaml:debug_notify_test"
)

SOURCE_FILE_LIST=""
for entry in "${SOURCES[@]}"; do
    SOURCE_FILE_LIST="${SOURCE_FILE_LIST}${SOURCE_FILE_LIST:+, }${entry%%:*}"
done

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
    local id=$2

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

for entry in "${SOURCES[@]}"; do
    add_to_master "${entry%%:*}" "${entry##*:}"
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

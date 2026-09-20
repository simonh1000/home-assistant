#!/usr/bin/env python3
import os
import sys
import yaml
import subprocess
from datetime import datetime
from pathlib import Path

# --- Configuration ---
OUTPUT_FILE = "automations.yaml"
SMB_TARGET = "//192.168.0.183/config"
SMB_HOST = "192.168.0.183"

def load_env():
    """Load HA_USER and HA_PASSWORD from .env file."""
    env_path = Path(".env")
    if not env_path.exists():
        print("Error: .env file not found.")
        sys.exit(1)
    
    config = {}
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                config[key] = value
    return config

def get_yaml_files():
    """Find all .yaml files in root directory excluding the output file."""
    files = sorted(Path(".").glob("*.yaml"))
    return [f for f in files if f.name != OUTPUT_FILE]

def generate_id(filename):
    """Create a Home Assistant ID from a filename (e.g. ev-safety.yaml -> ev_safety)."""
    return filename.replace(".yaml", "").replace("-", "_")

def combine():
    """Merge individual YAML files into a single master automations.yaml."""
    yaml_files = get_yaml_files()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_list = ", ".join([f.name for f in yaml_files])

    header = (
        "###############################################################################\n"
        "# AUTO-GENERATED MASTER AUTOMATIONS FILE - DO NOT EDIT MANUALLY\n"
        f"# Generated on: {timestamp}\n"
        f"# Source files: {file_list}\n"
        "#\n"
        "# To update this file:\n"
        "# 1. Edit the individual .yaml files in this directory.\n"
        "# 2. Run this script: ./combine.py\n"
        "###############################################################################\n\n"
    )

    master_list = []
    
    for yaml_file in yaml_files:
        print(f"Processing {yaml_file.name}...")
        try:
            with open(yaml_file) as f:
                content = yaml.safe_load(f)
                
                # Add the 'id' field required by Home Assistant for UI editing
                automation = {"id": generate_id(yaml_file.name)}
                automation.update(content)
                master_list.append(automation)
                
        except Exception as e:
            print(f"Error reading {yaml_file.name}: {e}")
            sys.exit(1)

    # Write the file
    with open(OUTPUT_FILE, "w") as f:
        f.write(header)
        yaml.dump(master_list, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f"\nDone! Consolidated file created at {OUTPUT_FILE}")
    return True

def deploy():
    """Upload the generated file to Home Assistant via SMB."""
    env = load_env()
    user = env.get("HA_USER")
    password = env.get("HA_PASSWORD")

    print("\nChecking for deployment path...")
    
    # 1. Check for existing macOS mount
    mount_output = subprocess.check_output(["mount"]).decode()
    existing_mount = None
    for line in mount_output.splitlines():
        if f"//{user}@{SMB_HOST}/config" in line:
            # Extract path (e.g. /Volumes/config)
            existing_mount = line.split(" on ")[1].split(" (")[0]
            break

    if existing_mount and os.path.exists(existing_mount):
        print(f"Found existing mount at {existing_mount}. Deploying...")
        try:
            subprocess.run(["cp", OUTPUT_FILE, existing_mount], check=True)
            print("Successfully deployed to existing mount.")
            return
        except subprocess.CalledProcessError:
            print("Warning: Copy failed. Attempting cleanup/remount...")

    # 2. Fallback: Manual mount (macOS style)
    print(f"Attempting fresh mount of {SMB_TARGET}...")
    temp_mount = subprocess.check_output(["mktemp", "-d"]).decode().strip()
    try:
        subprocess.run([
            "mount_smbfs", 
            f"//{user}:{password}@{SMB_HOST}/config", 
            temp_mount
        ], check=True)
        subprocess.run(["cp", OUTPUT_FILE, temp_mount], check=True)
        subprocess.run(["umount", temp_mount], check=True)
        print(f"Successfully deployed to {SMB_TARGET}")
    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")
    finally:
        if os.path.exists(temp_mount):
            os.rmdir(temp_mount)

if __name__ == "__main__":
    should_deploy = "--deploy" in sys.argv
    
    if combine() and should_deploy:
        deploy()

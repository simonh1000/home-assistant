#!/usr/bin/env python3
import os
import sys
import yaml
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# --- Configuration ---
DIST_DIR = Path("dist")
AUTOMATIONS_FILE = DIST_DIR / "automations.yaml"
SCRIPTS_FILE = DIST_DIR / "scripts.yaml"
HELPERS_FILE = DIST_DIR / "helpers.yaml"
HELPERS_SOURCE = Path("config/helpers.yaml")
CONFIG_FILE = DIST_DIR / "configuration.yaml"
CONFIG_SOURCE = Path("config/configuration.yaml")
SMB_TARGET = "//192.168.0.183/config"
SMB_HOST = "192.168.0.183"

def load_env():
    """Load HA_USER and HA_PASSWORD from .env file."""
    env_path = Path(".env")
    if not env_path.exists():
        print("Error: .env file not found.")
        sys.exit(1)
    
    config = {}
    current_key = None
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" in line:
                key, value = line.split("=", 1)
                config[key] = value
                current_key = key
            elif current_key:
                # Append to previous key (handles multi-line tokens)
                config[current_key] += line
    return config

def get_yaml_files():
    """Find all .yaml files and split them into automations and scripts."""
    all_files = sorted(Path(".").glob("*.yaml"))
    
    automations = []
    scripts = []
    
    for f in all_files:
        if f.name in ["automations.yaml", "scripts.yaml"]:
            continue
        
        if f.name.endswith(".script.yaml"):
            scripts.append(f)
        else:
            automations.append(f)
            
    return automations, scripts

def generate_id(filename):
    """Create a Home Assistant ID from a filename (e.g. ev-safety.yaml -> ev_safety)."""
    clean_name = filename.replace(".script.yaml", "").replace(".yaml", "")
    return clean_name.replace("-", "_")

def str_presenter(dumper, data):
    """Force YAML to use block scalars (|) for strings with newlines or single quotes to avoid escaping."""
    if "\n" in data or "'" in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)

def write_combined_file(output_path, files, is_script=False, version_tag=None):
    if not files:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    header = "# AUTO-GENERATED — DO NOT EDIT MANUALLY.\n"
    if version_tag:
        header += f"# Version: {version_tag}\n"
        header += f"# Deployed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "# Edit the individual source files instead.\n\n"

    if is_script:
        master_data = {}
    else:
        master_data = []

    for yaml_file in files:
        print(f"Processing {yaml_file.name}...")
        try:
            with open(yaml_file) as f:
                content = yaml.safe_load(f)
                file_id = generate_id(yaml_file.name)

                if is_script:
                    master_data[file_id] = content
                else:
                    automation = {"id": file_id}
                    automation.update(content)
                    master_data.append(automation)

        except Exception as e:
            print(f"Error reading {yaml_file.name}: {e}")
            sys.exit(1)

    with open(output_path, "w") as f:
        f.write(header)
        yaml.dump(master_data, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f"Done! Consolidated file created at {output_path}")
    return True

def combine(version_tag=None):
    """Handle the combination of both automations and scripts."""
    automations, scripts = get_yaml_files()
    
    a_success = write_combined_file(AUTOMATIONS_FILE, automations, is_script=False, version_tag=version_tag)
    s_success = write_combined_file(SCRIPTS_FILE, scripts, is_script=True, version_tag=version_tag)
    
    if version_tag:
        with open(DIST_DIR / "version.txt", "w") as f:
            f.write(version_tag)
    
    # Copy helpers.yaml to dist
    if HELPERS_SOURCE.exists():
        print(f"Copying {HELPERS_SOURCE} to {HELPERS_FILE}...")
        import shutil
        shutil.copy2(HELPERS_SOURCE, HELPERS_FILE)
    
    # Copy configuration.yaml to dist
    if CONFIG_SOURCE.exists():
        print(f"Copying {CONFIG_SOURCE} to {CONFIG_FILE}...")
        import shutil
        shutil.copy2(CONFIG_SOURCE, CONFIG_FILE)
    
    return a_success or s_success

def deploy(files_to_deploy):
    """Upload the generated files to Home Assistant via SMB."""
    env = load_env()
    user = env.get("HA_USER")
    password = env.get("HA_PASSWORD")

    print("\nChecking for deployment path...")
    
    # 1. Check for existing macOS mount
    mount_output = subprocess.check_output(["mount"]).decode()
    existing_mount = None
    for line in mount_output.splitlines():
        if f"//{user}@{SMB_HOST}/config" in line:
            existing_mount = line.split(" on ")[1].split(" (")[0]
            break

    if existing_mount and os.path.exists(existing_mount):
        print(f"Found existing mount at {existing_mount}. Deploying...")
        for f in files_to_deploy:
            if f.exists():
                print(f"Copying {f}...")
                subprocess.run(["cp", str(f), existing_mount], check=True)
        print("Successfully deployed to existing mount.")
        return

    # 2. Fallback: Manual mount (macOS style)
    print(f"Attempting fresh mount of {SMB_TARGET}...")
    temp_mount = subprocess.check_output(["mktemp", "-d"]).decode().strip()
    try:
        subprocess.run([
            "mount_smbfs", 
            f"//{user}:{password}@{SMB_HOST}/config", 
            temp_mount
        ], check=True)
        
        for f in files_to_deploy:
            if f.exists():
                print(f"Copying {f}...")
                subprocess.run(["cp", str(f), temp_mount], check=True)
        
        subprocess.run(["umount", temp_mount], check=True)
        print(f"Successfully deployed to {SMB_TARGET}")
    except subprocess.CalledProcessError as e:
        print(f"Deployment failed: {e}")
    finally:
        if os.path.exists(temp_mount):
            os.rmdir(temp_mount)

def reload_ha_yaml():
    """Trigger a reload of automations and scripts via the HA API."""
    env = load_env()
    token = env.get("HA_DEPLOY")
    if not token:
        print("\nNo HA_DEPLOY token found in .env, skipping API reload.")
        return

    print("\nTriggering Home Assistant YAML reload via API...")
    
    headers = [
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
    ]
    
    # "homeassistant/reload_core_config" reloads helpers (input_text, etc.)
    services = ["automation/reload", "script/reload", "homeassistant/reload_core_config"]
    
    for service in services:
        url = f"http://{SMB_HOST}:8123/api/services/{service}"
        print(f"Reloading {service}...")
        try:
            subprocess.run([
                "curl", "-s", "-X", "POST",
                *headers,
                url
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to reload {service}: {e}")

def update_ha_version_state(version_tag):
    """Update input_text entities in HA with the new version info."""
    env = load_env()
    token = env.get("HA_DEPLOY")
    if not token:
        return

    # Use "N/A" or "Latest" if no tag provided, so UI isn't "unknown"
    v_value = version_tag if version_tag else "Latest (No Tag)"
    now = datetime.now().isoformat()
    
    updates = [
        ("input_text.config_version", v_value),
        ("input_text.config_deployed", now),
    ]

    headers = [
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
    ]

    for entity_id, value in updates:
        url = f"http://{SMB_HOST}:8123/api/states/{entity_id}"
        data = f'{{"state": "{value}"}}'
        try:
            subprocess.run([
                "curl", "-s", "-X", "POST",
                *headers,
                "-d", data,
                url
            ], check=True)
            print(f"Updated {entity_id} to {value}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update {entity_id}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Combine and deploy HA config.")
    parser.add_argument("--deploy", action="store_true", help="Upload to Home Assistant")
    parser.add_argument("--version-tag", "-v", help="Version number (e.g. 1.0.1)")
    
    args = parser.parse_args()
    
    if args.deploy and not args.version_tag:
        print("Error: --version-tag (-v) is required when using --deploy.")
        sys.exit(1)
    
    if combine(version_tag=args.version_tag):
        if args.deploy:
            deploy([AUTOMATIONS_FILE, SCRIPTS_FILE, HELPERS_FILE, CONFIG_FILE])
            reload_ha_yaml()
            update_ha_version_state(args.version_tag)
        

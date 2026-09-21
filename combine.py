#!/usr/bin/env python3
import os
import sys
import yaml
import subprocess
from datetime import datetime
from pathlib import Path

# --- Configuration ---
DIST_DIR = Path("dist")
AUTOMATIONS_FILE = DIST_DIR / "automations.yaml"
SCRIPTS_FILE = DIST_DIR / "scripts.yaml"
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

def write_combined_file(output_path, files, is_script=False):
    if not files:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)

    header = "# AUTO-GENERATED — DO NOT EDIT MANUALLY. Edit the individual source files instead.\n\n"

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

def combine():
    """Handle the combination of both automations and scripts."""
    automations, scripts = get_yaml_files()
    
    a_success = write_combined_file(AUTOMATIONS_FILE, automations, is_script=False)
    s_success = write_combined_file(SCRIPTS_FILE, scripts, is_script=True)
    
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

def print_reload_reminder():
    """Print a prominent reminder to reload YAML in Home Assistant."""
    print("\n" + "="*60)
    print("REMINDER: You must RELOAD your YAML in Home Assistant:")
    print("Settings -> Tools -> YAML -> AUTOMATIONS & SCRIPTS")
    print("="*60 + "\n")

if __name__ == "__main__":
    should_deploy = "--deploy" in sys.argv
    
    if combine():
        if should_deploy:
            deploy([AUTOMATIONS_FILE, SCRIPTS_FILE])
        
        print_reload_reminder()

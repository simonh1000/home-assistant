#!/usr/bin/env python3
import os
import shutil
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

# --- Configuration ---
VERSION_FILE = Path("VERSION")
DIST_DIR = Path("dist")
# configuration.yaml pulls these in via !include_dir_list / !include_dir_merge_named,
# which HA resolves relative to the config root.
AUTOMATIONS_SOURCE = Path("src/automations")
AUTOMATIONS_DIST = DIST_DIR / "automations"
SCRIPTS_SOURCE = Path("src/scripts")
SCRIPTS_DIST = DIST_DIR / "scripts"
HELPERS_SOURCE = Path("src/helpers")
HELPERS_DIST = DIST_DIR / "helpers"
CONFIG_FILE = DIST_DIR / "configuration.yaml"
CONFIG_SOURCE = Path("src/configuration.yaml")
DASHBOARD_FILE = DIST_DIR / "ui-lovelace.yaml"
DASHBOARD_SOURCE = Path("src/ui-lovelace.yaml")
WWW_SOURCE = Path("src/www")
WWW_DIST = DIST_DIR / "www"
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

def get_current_version():
    """Read the version from the VERSION file."""
    if not VERSION_FILE.exists():
        return "0.0.1"
    return VERSION_FILE.read_text().strip()

def save_version(version):
    """Write the new version to the VERSION file."""
    VERSION_FILE.write_text(f"{version}\n")

def copy_tree(source_dir, dist_dir):
    """Mirror a source directory into dist, replacing whatever was there before."""
    if not source_dir.exists():
        return False
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, dist_dir)
    
    # Just count files for feedback
    file_count = sum(1 for p in dist_dir.rglob('*') if p.is_file())
    print(f"  + {dist_dir.relative_to(DIST_DIR.parent)}/ ({file_count} files)")
    return True

def combine(version_tag=None):
    """Stage everything HA needs into dist/, mirroring the src/ layout configuration.yaml expects."""
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    print("Staging files to /dist...")
    a_success = copy_tree(AUTOMATIONS_SOURCE, AUTOMATIONS_DIST)
    s_success = copy_tree(SCRIPTS_SOURCE, SCRIPTS_DIST)
    h_success = copy_tree(HELPERS_SOURCE, HELPERS_DIST)

    if version_tag:
        with open(DIST_DIR / "version.txt", "w") as f:
            f.write(version_tag)

    # Copy configuration.yaml to dist
    if CONFIG_SOURCE.exists():
        shutil.copy2(CONFIG_SOURCE, CONFIG_FILE)
        print(f"  + {CONFIG_FILE.relative_to(DIST_DIR.parent)}")

    # Copy ui-lovelace.yaml to dist
    if DASHBOARD_SOURCE.exists():
        shutil.copy2(DASHBOARD_SOURCE, DASHBOARD_FILE)
        print(f"  + {DASHBOARD_FILE.relative_to(DIST_DIR.parent)}")

    # Copy www directory to dist
    if WWW_SOURCE.exists():
        copy_tree(WWW_SOURCE, WWW_DIST)

    return a_success or s_success or h_success or m_success

def deploy_items(files_to_deploy, target_dir):
    """Copy files as-is; sync directories with --delete so files removed locally
    (e.g. a deleted automation) don't linger on the HA host."""
    for f in files_to_deploy:
        if not f.exists():
            continue
        if f.is_dir():
            print(f"Syncing {f.name}/...")
            dest = os.path.join(target_dir, f.name) + "/"
            subprocess.run(["rsync", "-a", "--delete", f"{f}/", dest], check=True)
        else:
            print(f"Copying {f.name}...")
            subprocess.run(["cp", str(f), target_dir], check=True)

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
        deploy_items(files_to_deploy, existing_mount)
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

        deploy_items(files_to_deploy, temp_mount)

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
    parser.add_argument("--version-tag", "-v", help="Version number (e.g. 1.0.1). If omitted during deploy, it auto-bumps.")
    
    args = parser.parse_args()
    
    current_v = get_current_version()
    target_v = args.version_tag or current_v

    if args.version_tag:
        print(f"Updating VERSION file to: {target_v}")
        save_version(target_v)
    
    print(f"Using version: {target_v}")
    
    if combine(version_tag=target_v):
        if args.deploy:
            deploy([
                AUTOMATIONS_DIST,
                SCRIPTS_DIST,
                HELPERS_DIST,
                CONFIG_FILE,
                DASHBOARD_FILE,
                WWW_DIST
            ])
            reload_ha_yaml()
            update_ha_version_state(target_v)
        

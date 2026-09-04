#!/usr/bin/env bash
# ==============================================================================
# GeoTani — VPS Multi-User Creation & Permission Provisioning Script
#
# Usage:
#   sudo ./scripts/create_vps_user.sh <username> [options]
#
# Options:
#   --ssh-key "ssh-ed25519 AAAAC3NzaC1..."   Inject public SSH key directly
#   --role [docker|admin|readonly]           Set user permission role (default: docker)
#   --project-dir "/opt/geotani"             Grant write access to project directory
#
# Examples:
#   sudo ./scripts/create_vps_user.sh alice --role docker --ssh-key "ssh-ed25519 AAAAB3..."
#   sudo ./scripts/create_vps_user.sh bob --role admin
# ==============================================================================

set -e

# Ensure script is run with sudo/root privileges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Please run this script with sudo or as root:"
    echo "   sudo $0 $@"
    exit 1
fi

USERNAME="$1"
if [ -z "$USERNAME" ]; then
    echo "================================================================="
    echo "       👥 GeoTani VPS User Account Provisioning Tool            "
    echo "================================================================="
    echo "Usage: sudo $0 <username> [options]"
    echo ""
    echo "Options:"
    echo "  --ssh-key \"<public-key>\"    Public SSH key string"
    echo "  --role [docker|admin|readonly] Permission level (default: docker)"
    echo "  --project-dir <path>          Project path to share (default: /opt/geotani)"
    echo ""
    exit 1
fi
shift

ROLE="docker"
SSH_KEY=""
PROJECT_DIR="/opt/geotani"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --ssh-key)
            SSH_KEY="$2"
            shift 2
            ;;
        --role)
            ROLE="$2"
            shift 2
            ;;
        --project-dir)
            PROJECT_DIR="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "================================================================="
echo " Creating user account: $USERNAME (Role: $ROLE)"
echo "================================================================="

# 1. Create user if they don't already exist
if id "$USERNAME" &>/dev/null; then
    echo "ℹ️  User '$USERNAME' already exists. Updating permissions and SSH keys..."
else
    # Create user with home directory and bash shell
    useradd -m -s /bin/bash "$USERNAME"
    echo "✓ Created user account: $USERNAME"
fi

# 2. Configure Permissions based on Role
case "$ROLE" in
    admin)
        echo "Granting full sudo and Docker privileges..."
        usermod -aG sudo "$USERNAME" 2>/dev/null || usermod -aG wheel "$USERNAME" 2>/dev/null
        if getent group docker >/dev/null; then
            usermod -aG docker "$USERNAME"
        fi
        echo "✓ Added $USERNAME to 'sudo' and 'docker' groups."
        ;;
    docker)
        echo "Granting Docker management access (can run containers without sudo)..."
        if ! getent group docker >/dev/null; then
            groupadd docker
        fi
        usermod -aG docker "$USERNAME"
        echo "✓ Added $USERNAME to 'docker' group."
        ;;
    readonly)
        echo "Restricting user to standard unprivileged access..."
        ;;
    *)
        echo "❌ Error: Invalid role '$ROLE'. Choose 'admin', 'docker', or 'readonly'."
        exit 1
        ;;
esac

# 3. Configure Project Directory Access
if [ -d "$PROJECT_DIR" ]; then
    echo "Configuring shared access to $PROJECT_DIR..."
    # Ensure project group exists or use docker group
    chgrp -R docker "$PROJECT_DIR" 2>/dev/null || true
    chmod -R g+rwX "$PROJECT_DIR" 2>/dev/null || true
    echo "✓ Granted group permissions on $PROJECT_DIR."
fi

# 4. Set Up SSH Directory & Keys
USER_HOME=$(eval echo "~$USERNAME")
SSH_DIR="$USER_HOME/.ssh"
AUTH_KEYS="$SSH_DIR/authorized_keys"

mkdir -p "$SSH_DIR"
chmod 700 "$SSH_DIR"

if [ -n "$SSH_KEY" ]; then
    echo "$SSH_KEY" >> "$AUTH_KEYS"
    echo "✓ Injected provided SSH public key into $AUTH_KEYS."
else
    touch "$AUTH_KEYS"
    echo ""
    echo "⚠️  No SSH key was passed via --ssh-key."
    echo "   You can add their public key now, or paste it later into:"
    echo "   $AUTH_KEYS"
    echo ""
fi

# Ensure unique keys and correct permissions
sort -u "$AUTH_KEYS" -o "$AUTH_KEYS" 2>/dev/null || true
chmod 600 "$AUTH_KEYS"
chown -R "$USERNAME:$USERNAME" "$SSH_DIR"

echo "================================================================="
echo " 🎉 Account Setup Complete for: $USERNAME"
echo "================================================================="
echo " User: $USERNAME"
echo " Role: $ROLE"
echo " SSH Authorized Keys: $AUTH_KEYS"
echo ""
echo " How the new user connects from their machine:"
echo "   ssh $USERNAME@YOUR_VPS_IP"
echo "================================================================="

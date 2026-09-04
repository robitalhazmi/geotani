#!/usr/bin/env bash
# ==============================================================================
# GeoTani — VPS User Management Tool
#
# Commands:
#   sudo ./scripts/manage_vps_users.sh --list
#   sudo ./scripts/manage_vps_users.sh --add <username> [--role docker|admin|readonly] [--ssh-key "key"]
#   sudo ./scripts/manage_vps_users.sh --delete <username> [--remove-home]
#   sudo ./scripts/manage_vps_users.sh --lock <username>
#   sudo ./scripts/manage_vps_users.sh --unlock <username>
# ==============================================================================

set -e

# Ensure script is run with sudo/root privileges
if [ "$EUID" -ne 0 ]; then
    echo "❌ Error: Please run this script with sudo or as root:"
    echo "   sudo $0 $@"
    exit 1
fi

ACTION="$1"

print_help() {
    echo "================================================================="
    echo "         👥 GeoTani VPS User Account Management Tool             "
    echo "================================================================="
    echo "Usage:"
    echo "  sudo $0 --list                                 List all user accounts & roles"
    echo "  sudo $0 --add <username> [options]             Create new user account"
    echo "  sudo $0 --delete <username> [--remove-home]    Remove user account"
    echo "  sudo $0 --lock <username>                      Temporarily disable access"
    echo "  sudo $0 --unlock <username>                    Restore disabled access"
    echo ""
    echo "Options for --add:"
    echo "  --role [docker|admin|readonly]                 Role level (default: docker)"
    echo "  --ssh-key \"<ssh-public-key-string>\"           Inject public SSH key"
    echo "  --project-dir <path>                           Project path (default: /opt/geotani)"
    echo "================================================================="
}

if [ -z "$ACTION" ] || [ "$ACTION" = "--help" ] || [ "$ACTION" = "-h" ]; then
    print_help
    exit 0
fi

shift

case "$ACTION" in
    --list|-l)
        echo "================================================================="
        echo " 👥 Human User Accounts on VPS (UID >= 1000)"
        echo "================================================================="
        printf "%-18s %-8s %-24s %-12s\n" "USERNAME" "UID" "GROUPS" "SSH KEYS"
        echo "-----------------------------------------------------------------"
        
        while IFS=: read -r username _ uid _ _ home shell; do
            if [ "$uid" -ge 1000 ] && [ "$uid" -lt 65534 ] && [ "$username" != "nobody" ]; then
                user_groups=$(id -Gn "$username" 2>/dev/null | tr ' ' ',' || echo "none")
                key_count=0
                if [ -f "$home/.ssh/authorized_keys" ]; then
                    key_count=$(grep -c '^ssh-' "$home/.ssh/authorized_keys" 2>/dev/null || echo 0)
                fi
                printf "%-18s %-8s %-24s %-12s\n" "$username" "$uid" "$user_groups" "$key_count key(s)"
            fi
        done < /etc/passwd
        echo "================================================================="
        ;;

    --add|-a)
        USERNAME="$1"
        if [ -z "$USERNAME" ]; then
            echo "❌ Error: Username required. Usage: sudo $0 --add <username> [options]"
            exit 1
        fi
        shift

        ROLE="docker"
        SSH_KEY=""
        PROJECT_DIR="/opt/geotani"

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

        echo "Creating user account: $USERNAME (Role: $ROLE)..."
        if id "$USERNAME" &>/dev/null; then
            echo "ℹ️  User '$USERNAME' already exists. Updating permissions..."
        else
            useradd -m -s /bin/bash "$USERNAME"
            echo "✓ Created user account: $USERNAME"
        fi

        case "$ROLE" in
            admin)
                usermod -aG sudo "$USERNAME" 2>/dev/null || usermod -aG wheel "$USERNAME" 2>/dev/null
                if getent group docker >/dev/null; then
                    usermod -aG docker "$USERNAME"
                fi
                echo "✓ Granted full sudo + docker admin privileges."
                ;;
            docker)
                if ! getent group docker >/dev/null; then
                    groupadd docker
                fi
                usermod -aG docker "$USERNAME"
                echo "✓ Granted docker management privileges."
                ;;
            readonly)
                echo "✓ Configured as unprivileged user."
                ;;
            *)
                echo "❌ Invalid role '$ROLE'. Choose 'admin', 'docker', or 'readonly'."
                exit 1
                ;;
        esac

        if [ -d "$PROJECT_DIR" ]; then
            chgrp -R docker "$PROJECT_DIR" 2>/dev/null || true
            chmod -R g+rwX "$PROJECT_DIR" 2>/dev/null || true
        fi

        USER_HOME=$(eval echo "~$USERNAME")
        SSH_DIR="$USER_HOME/.ssh"
        AUTH_KEYS="$SSH_DIR/authorized_keys"

        mkdir -p "$SSH_DIR"
        chmod 700 "$SSH_DIR"

        if [ -n "$SSH_KEY" ]; then
            echo "$SSH_KEY" >> "$AUTH_KEYS"
            sort -u "$AUTH_KEYS" -o "$AUTH_KEYS" 2>/dev/null || true
            echo "✓ Added SSH public key."
        else
            touch "$AUTH_KEYS"
        fi

        chmod 600 "$AUTH_KEYS"
        chown -R "$USERNAME:$USERNAME" "$SSH_DIR"

        echo "✓ Account setup complete for: $USERNAME"
        ;;

    --delete|-d|--remove)
        USERNAME="$1"
        REMOVE_HOME=false
        if [ -z "$USERNAME" ]; then
            echo "❌ Error: Username required. Usage: sudo $0 --delete <username> [--remove-home]"
            exit 1
        fi
        shift

        if [ "$1" = "--remove-home" ] || [ "$1" = "-r" ]; then
            REMOVE_HOME=true
        fi

        if ! id "$USERNAME" &>/dev/null; then
            echo "❌ Error: User '$USERNAME' does not exist."
            exit 1
        fi

        if [ "$USERNAME" = "root" ]; then
            echo "❌ Error: Cannot delete root user."
            exit 1
        fi

        echo "Terminating any running processes for '$USERNAME'..."
        killall -u "$USERNAME" 2>/dev/null || true
        sleep 1

        if [ "$REMOVE_HOME" = true ]; then
            echo "Deleting user '$USERNAME' and removing home directory..."
            deluser --remove-home "$USERNAME" 2>/dev/null || userdel -r "$USERNAME"
            echo "✓ User '$USERNAME' and home directory deleted successfully."
        else
            echo "Deleting user '$USERNAME' (preserving home directory)..."
            deluser "$USERNAME" 2>/dev/null || userdel "$USERNAME"
            echo "✓ User '$USERNAME' deleted (files preserved)."
        fi
        ;;

    --lock)
        USERNAME="$1"
        if [ -z "$USERNAME" ] || ! id "$USERNAME" &>/dev/null; then
            echo "❌ Error: Valid username required."
            exit 1
        fi
        usermod -L "$USERNAME" 2>/dev/null || passwd -l "$USERNAME"
        # Temporarily disable authorized_keys
        USER_HOME=$(eval echo "~$USERNAME")
        if [ -f "$USER_HOME/.ssh/authorized_keys" ]; then
            mv "$USER_HOME/.ssh/authorized_keys" "$USER_HOME/.ssh/authorized_keys.disabled"
        fi
        echo "✓ User '$USERNAME' has been locked (SSH & password access disabled)."
        ;;

    --unlock)
        USERNAME="$1"
        if [ -z "$USERNAME" ] || ! id "$USERNAME" &>/dev/null; then
            echo "❌ Error: Valid username required."
            exit 1
        fi
        usermod -U "$USERNAME" 2>/dev/null || passwd -u "$USERNAME"
        USER_HOME=$(eval echo "~$USERNAME")
        if [ -f "$USER_HOME/.ssh/authorized_keys.disabled" ]; then
            mv "$USER_HOME/.ssh/authorized_keys.disabled" "$USER_HOME/.ssh/authorized_keys"
        fi
        echo "✓ User '$USERNAME' has been unlocked."
        ;;

    *)
        echo "❌ Unknown command '$ACTION'."
        print_help
        exit 1
        ;;
esac

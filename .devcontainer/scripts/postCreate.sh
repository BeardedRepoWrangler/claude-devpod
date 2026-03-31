#!/usr/bin/env bash
set -euo pipefail

echo "=== Claude DevPod: Post-create setup ==="

# Step 1: Install Claude Code via official install script
echo "--- [1/4] Installing Claude Code..."
curl -fsSL https://claude.ai/install.sh | bash

# Step 2: Verify Claude Code installed successfully
echo "--- [2/4] Verifying Claude Code..."
claude --version

# Step 3: Configure git safe.directory (required for bind-mounted Windows paths)
echo "--- [3/4] Configuring git safe.directory..."
git config --global --add safe.directory '*'

# Step 4: Configure user-level Podman storage (skip if already configured)
echo "--- [4/4] Configuring Podman user storage..."
if [ ! -f "${HOME}/.config/containers/storage.conf" ]; then
    mkdir -p "${HOME}/.config/containers"
    cat > "${HOME}/.config/containers/storage.conf" << 'EOF'
[storage]
driver = "overlay"

[storage.options.overlay]
mount_program = "/usr/bin/fuse-overlayfs"
EOF
    echo "    Podman user storage configured."
else
    echo "    Podman user storage already configured, skipping."
fi

echo ""
echo "=== Claude DevPod ready! ==="
echo "  claude: $(claude --version)"
echo "  node:   $(node --version)"
echo "  python: $(python3 --version)"
echo "  podman: $(podman --version)"
echo "  git:    $(git --version)"

#!/usr/bin/env bash
set -euo pipefail

echo "=== Claude DevPod: Post-create setup ==="

# Step 1: Install Claude Code via official install script
echo "--- [1/5] Installing Claude Code..."
curl -fsSL https://claude.ai/install.sh | bash

# Step 2: Verify Claude Code installed successfully
echo "--- [2/5] Verifying Claude Code..."
claude --version

# Step 3: Install GitHub CLI (gh)
echo "--- [3/5] Installing GitHub CLI..."
if ! command -v gh &>/dev/null; then
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt-get update -qq && sudo apt-get install -y gh
    echo "    GitHub CLI installed: $(gh --version | head -1)"
else
    echo "    GitHub CLI already installed: $(gh --version | head -1)"
fi

# Step 4: Configure git safe.directory (required for bind-mounted Windows paths)
echo "--- [4/5] Configuring git safe.directory..."
git config --global --add safe.directory '*'

# Step 5: Configure user-level Podman storage (skip if already configured)
echo "--- [5/5] Configuring Podman user storage..."
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
echo "  gh:     $(gh --version | head -1)"
echo "  node:   $(node --version)"
echo "  python: $(python3 --version)"
echo "  podman: $(podman --version)"
echo "  git:    $(git --version)"

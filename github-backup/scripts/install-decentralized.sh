#!/bin/bash
# GitHub Organization Backup System - Decentralized Dependencies Installation

set -e

echo "🌐 Installing Decentralized Backup Dependencies..."

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*)    MACHINE=Cygwin;;
    MINGW*)     MACHINE=MinGw;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "📋 Detected OS: $MACHINE"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Node.js if not present
install_nodejs() {
    if ! command_exists node; then
        echo "📦 Installing Node.js..."
        if [ "$MACHINE" = "Mac" ]; then
            # macOS
            if command_exists brew; then
                brew install node
            else
                echo "❌ Homebrew not found. Please install Node.js manually: https://nodejs.org/"
                return 1
            fi
        elif [ "$MACHINE" = "Linux" ]; then
            # Linux
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        else
            echo "❌ Please install Node.js manually: https://nodejs.org/"
            return 1
        fi
    else
        echo "✅ Node.js already installed: $(node --version)"
    fi
}

# Function to install Go if not present
install_go() {
    if ! command_exists go; then
        echo "📦 Installing Go..."
        if [ "$MACHINE" = "Mac" ]; then
            # macOS
            if command_exists brew; then
                brew install go
            else
                echo "❌ Homebrew not found. Please install Go manually: https://golang.org/"
                return 1
            fi
        elif [ "$MACHINE" = "Linux" ]; then
            # Linux
            wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
            sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
            echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
            source ~/.bashrc
            rm go1.21.0.linux-amd64.tar.gz
        else
            echo "❌ Please install Go manually: https://golang.org/"
            return 1
        fi
    else
        echo "✅ Go already installed: $(go version)"
    fi
}

# Install Radicle
install_radicle() {
    echo "🔧 Installing Radicle..."
    if command_exists rad; then
        echo "✅ Radicle already installed: $(rad --version)"
    else
        curl -sSf https://radicle.xyz/install | sh
        echo "✅ Radicle installed successfully"
        echo "💡 Run 'source ~/.zshenv && rad auth' to set up your identity"
    fi
}

# Install IPFS
install_ipfs() {
    echo "🔧 Installing IPFS..."
    if command_exists ipfs; then
        echo "✅ IPFS already installed: $(ipfs version)"
    else
        if [ "$MACHINE" = "Mac" ]; then
            # macOS
            if command_exists brew; then
                brew install ipfs
            else
                echo "❌ Homebrew not found. Please install IPFS manually: https://ipfs.io/"
                return 1
            fi
        elif [ "$MACHINE" = "Linux" ]; then
            # Linux
            wget https://dist.ipfs.io/go-ipfs/v0.20.0/go-ipfs_v0.20.0_linux-amd64.tar.gz
            tar -xvzf go-ipfs_v0.20.0_linux-amd64.tar.gz
            cd go-ipfs
            sudo bash install.sh
            cd ..
            rm -rf go-ipfs go-ipfs_v0.20.0_linux-amd64.tar.gz
        else
            echo "❌ Please install IPFS manually: https://ipfs.io/"
            return 1
        fi
        
        # Initialize IPFS
        if [ ! -d ~/.ipfs ]; then
            echo "🔧 Initializing IPFS..."
            ipfs init
        fi
        
        echo "✅ IPFS installed and initialized"
        echo "💡 Run 'ipfs daemon' to start the IPFS node"
    fi
}

# Install GitTorrent
install_gittorrent() {
    echo "🔧 Installing GitTorrent..."
    if command_exists git-torrent; then
        echo "✅ GitTorrent already installed: $(git-torrent --version)"
    else
        install_nodejs
        echo "⚠️  GitTorrent npm package not available. Skipping installation."
        echo "💡 GitTorrent can be installed manually from: https://github.com/cjb/GitTorrent"
    fi
}

# Install Dat CLI
install_dat() {
    echo "🔧 Installing Dat CLI..."
    if command_exists dat; then
        echo "✅ Dat CLI already installed: $(dat --version)"
    else
        install_nodejs
        npm install -g dat
        echo "✅ Dat CLI installed successfully"
    fi
}

# Install all decentralized tools
echo "🚀 Installing all decentralized backup tools..."

install_radicle
install_ipfs
install_gittorrent
install_dat

echo ""
echo "🎉 Decentralized backup dependencies installed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Set up Radicle identity: rad auth"
echo "2. Start IPFS daemon: ipfs daemon &"
echo "3. Configure your backup targets in config.yaml"
echo "4. Test connections: python scripts/test-connections.py"
echo ""
echo "📚 Documentation:"
echo "- Radicle: https://radicle.xyz/docs"
echo "- IPFS: https://docs.ipfs.io/"
echo "- GitTorrent: https://github.com/cjb/GitTorrent"
echo "- Dat: https://docs.dat.foundation/" 
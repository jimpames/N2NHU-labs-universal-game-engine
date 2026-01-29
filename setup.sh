#!/bin/bash
# Quick setup script for ZORK game

echo "🎮 Setting up ZORK Text Adventure Game..."
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --break-system-packages

# Generate SSH key if needed
if [ ! -f ssh_host_key ]; then
    echo "🔑 Generating SSH host key..."
    ssh-keygen -t rsa -f ssh_host_key -N "" -q
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 To play locally:"
echo "   ./run_game.py"
echo ""
echo "🌐 To run SSH server:"
echo "   ./ssh_server.py"
echo "   Then connect with: ssh -p 2222 player@localhost"
echo ""
echo "📚 Read README.md for architecture details and teaching points!"
echo ""

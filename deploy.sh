#!/bin/bash
# Quick deployment script for Fly.io

echo "🚀 Deploying Forensic CTF to Fly.io..."
echo ""

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    echo "❌ Fly.io CLI not found. Install it first:"
    echo "   https://fly.io/docs/hands-on/install-flyctl/"
    exit 1
fi

# Check if logged in
if ! flyctl auth whoami &> /dev/null; then
    echo "🔐 Please login to Fly.io first:"
    flyctl auth login
fi

echo "✅ Fly.io CLI ready"
echo ""

# Deploy
echo "📦 Building and deploying..."
flyctl deploy --local-only

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Check status:"
echo "   flyctl status"
echo ""
echo "📋 View logs:"
echo "   flyctl logs"
echo ""
echo "🌐 Your app:"
echo "   flyctl info"

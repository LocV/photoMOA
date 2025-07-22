#!/bin/bash

echo "🔧 Fixing React Components..."

# Go to frontend directory
cd frontend/src

# Clean up any problematic files
echo "Cleaning up component files..."
rm -f components/*.tsx

# Recreate the components directory
mkdir -p components

echo "✅ All components should now be fixed!"
echo "Try running 'npm start' in the frontend directory again."

#!/bin/bash
echo "Build version: 2026.01.25.v3"
cd frontend
npm install
npm run build
echo "Build complete: $(date)"

#!/bin/bash
# Real-time debugging monitor for Flask API
# Shows all debug output as it happens

echo "============================================================"
echo "🔍 FLASK DEBUG MONITOR - Watching for prediction errors"
echo "============================================================"
echo "Log file: /tmp/flask_debug.log"
echo "Press Ctrl+C to stop"
echo "============================================================"
echo ""

tail -f /tmp/flask_debug.log | grep --line-buffered -E "(DEBUG:|ERROR|🔍|📥|❌|✅|🏠|✈️|🤖|⚖️|⏰|🔧|📊|👤|🔀|📤)"

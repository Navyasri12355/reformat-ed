#!/bin/bash
# Migration script to complete frontend reorganization
# Run this from the project root: bash scripts/migrate-frontend.sh

echo "=== NeuraCore Frontend Migration ==="

# Move page components to pages/
echo "Moving page components..."
mv frontend/src/TeacherDash.jsx frontend/src/pages/TeacherDash.jsx
mv frontend/src/Quiz.jsx frontend/src/pages/Quiz.jsx
mv frontend/src/ADHDDash.jsx frontend/src/pages/ADHDDash.jsx
mv frontend/src/DyslexiaDash.jsx frontend/src/pages/DyslexiaDash.jsx
mv frontend/src/ASDDash.jsx frontend/src/pages/ASDDash.jsx

# Move api.js to utils/
echo "Moving api.js..."
mv frontend/src/api.js frontend/src/utils/api.js

# Move styles.css to styles/
echo "Moving styles.css..."
cp frontend/src/styles.css frontend/src/styles/global.css

echo "✅ Frontend migration complete!"
echo ""
echo "Next steps:"
echo "1. Update imports in pages/*.jsx to use ../utils/api.js"
echo "2. Update imports in pages/*.jsx to use ../styles/theme.js"
echo "3. Test: npm run dev"
echo "4. Remove old files if migration successful"

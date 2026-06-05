@echo off
REM Migration script for Windows
REM Run from project root: scripts\migrate-frontend.bat

echo === NeuraCore Frontend Migration (Windows) ===

echo Moving page components...
move frontend\src\TeacherDash.jsx frontend\src\pages\TeacherDash.jsx
move frontend\src\Quiz.jsx frontend\src\pages\Quiz.jsx
move frontend\src\ADHDDash.jsx frontend\src\pages\ADHDDash.jsx
move frontend\src\DyslexiaDash.jsx frontend\src\pages\DyslexiaDash.jsx
move frontend\src\ASDDash.jsx frontend\src\pages\ASDDash.jsx

echo Moving api.js...
move frontend\src\api.js frontend\src\utils\api.js

echo Moving styles.css...
copy frontend\src\styles.css frontend\src\styles\global.css

echo.
echo ✅ Frontend migration complete!
echo.
echo Next steps:
echo 1. Update imports in pages\*.jsx to use ../utils/api.js
echo 2. Update imports in pages\*.jsx to use ../styles/theme.js
echo 3. Test: npm run dev
echo 4. Remove old files if migration successful
pause

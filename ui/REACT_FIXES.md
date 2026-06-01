# Quick React Fix - Use index.html directly

The TypeScript path issue is a known Windows bug with react-scripts. 

## Option 1: Test with static HTML (FASTEST)
Just open the index.html directly in browser:
- Open: D:\Dev\repos\ednaficator\ui\index.html in Chrome
- This should load the React app (though without hot reload)

## Option 2: Use Vite instead (BETTER)
Replace react-scripts with Vite:

```bash
npm uninstall react-scripts
npm install vite @vitejs/plugin-react --save-dev

# Create vite.config.js:
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: { port: 3000 }
})

# Update package.json scripts:
"dev": "vite",
"build": "vite build"
```

## Option 3: Environment Variable Fix
Try this before npm run dev:
```bash
$env:SKIP_PREFLIGHT_CHECK="true"
npm run dev
```

## MEANWHILE: Test Backend
The Python backend should work fine:
```bash
cd D:\Dev\repos\ednaficator
python api_bridge.py
```

You can test it directly at: http://localhost:8000/docs

Set-Location "$PSScriptRoot\frontend"
if (!(Test-Path "node_modules")) { npm install }
if (!(Test-Path ".env.local")) { Copy-Item ".env.local.example" ".env.local" }
npm run dev

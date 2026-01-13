# Install RIG in development mode
# This makes the 'rig' command available globally

Write-Host "Installing RIG packages in development mode..." -ForegroundColor Cyan

# Install core packages
Write-Host "`nInstalling rig-core..." -ForegroundColor Yellow
pip install -e packages/rig-core

Write-Host "`nInstalling rig-cli..." -ForegroundColor Yellow
pip install -e packages/rig-cli

Write-Host "`nInstalling rig-protocol-rgp..." -ForegroundColor Yellow
pip install -e packages/rig-protocol-rgp

Write-Host "`nInstalling rig-bridge-mcp..." -ForegroundColor Yellow
pip install -e packages/rig-bridge-mcp

Write-Host "`n✓ Installation complete!" -ForegroundColor Green
Write-Host "`nYou can now use the 'rig' command:" -ForegroundColor Cyan
Write-Host "  rig --help" -ForegroundColor White
Write-Host "  rig packs --available" -ForegroundColor White
Write-Host "  rig install stripe" -ForegroundColor White


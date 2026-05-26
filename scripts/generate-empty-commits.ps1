param(
    [Parameter(Mandatory = $true)]
    [ValidateRange(1, 10000)]
    [int]$Count,

    [string]$Branch = "main",
    [string]$Remote = "origin",
    [string]$Account = "jerryosorio-corestory",
    [string]$MessagePrefix = "chore: external app sync marker",
    [switch]$Push
)

$ErrorActionPreference = "Stop"

Write-Host "Checking git branch..." -ForegroundColor Cyan
$currentBranch = (git branch --show-current).Trim()
if ($currentBranch -ne $Branch) {
    Write-Host "Switching branch from '$currentBranch' to '$Branch'..." -ForegroundColor Yellow
    git checkout $Branch
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to switch to branch '$Branch'."
    }
}

Write-Host "Switching GitHub CLI account to '$Account'..." -ForegroundColor Cyan
gh auth switch -u $Account | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to switch GitHub account to '$Account'."
}

Write-Host "Creating $Count empty commit(s)..." -ForegroundColor Cyan
for ($i = 1; $i -le $Count; $i++) {
    $message = "$MessagePrefix $i/$Count"
    git commit --allow-empty -m $message | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Failed creating commit $i of $Count."
    }
}

if ($Push) {
    Write-Host "Pushing to $Remote/$Branch..." -ForegroundColor Cyan
    git push $Remote $Branch | Out-Host
    if ($LASTEXITCODE -ne 0) {
        throw "Push failed to $Remote/$Branch."
    }
    Write-Host "Done: commits created and pushed." -ForegroundColor Green
} else {
    Write-Host "Done: commits created locally. Use 'git push $Remote $Branch' when ready." -ForegroundColor Green
}

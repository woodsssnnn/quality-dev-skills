# smoke-test.ps1 — 快速冒烟测试新子命令
param()
$ErrorActionPreference = "Continue"
$repo = "c:\Users\Admin\.agents\skills-source\quality-dev-skills"
$enforcer = "$repo\skills\quality-gate-workflow\scripts\gate-enforcer.py"
$tmp = Join-Path $env:TEMP "qgw-smoke-$(Get-Random)"

# Setup
New-Item -ItemType Directory "$tmp\docs\plans" -Force | Out-Null
New-Item -ItemType Directory "$tmp\docs\verification" -Force | Out-Null
New-Item -ItemType Directory "$tmp\docs\reports" -Force | Out-Null
New-Item -ItemType Directory "$tmp\docs\sessions" -Force | Out-Null
Push-Location $tmp

$pass = 0; $fail = 0

function Check($name, $result) {
    if ($result -match '"status":\s*"(OK|ALLOW)"') {
        $script:pass++
        Write-Host "  PASS $name" -ForegroundColor Green
    } else {
        $script:fail++
        Write-Host "  FAIL $name" -ForegroundColor Red
        Write-Host "       $result"
    }
}

Write-Host "=== CLI Smoke Test ==="

# 1. init gate2
$r = python $enforcer init --gate gate2 --mode impl 2>&1
Check "init gate2" $r

# 2. enter S0
$r = python $enforcer enter S0 2>&1
Check "enter S0" $r

# 3. complete S0
$r = python $enforcer complete S0 2>&1
Check "complete S0" $r

# 4. enter S1
$r = python $enforcer enter S1 2>&1
Check "enter S1" $r

# 5. complete S1
$r = python $enforcer complete S1 2>&1
Check "complete S1" $r

# 6. prd-changed cosmetic (no step reset)
$r = python $enforcer prd-changed --impact cosmetic --scope "§2.3" 2>&1
Check "prd-changed cosmetic" $r

# 7. plan-tweak
$r = python $enforcer plan-tweak --reason "字段名修正" --scope "ch-2.3" 2>&1
Check "plan-tweak" $r

# 8. prd-changed minor (should reset S4)
$r = python $enforcer prd-changed --impact minor --scope "§3.1" 2>&1
Check "prd-changed minor" $r

# 9. status
$r = python $enforcer status 2>&1
Check "status" $r

# 10. self-check
$r = python $enforcer self-check 2>&1
Check "self-check" $r

# 11. resume
$r = python $enforcer resume 2>&1
Check "resume" $r

Pop-Location
Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Results: $pass passed, $fail failed ==="
if ($fail -gt 0) { exit 1 } else { exit 0 }

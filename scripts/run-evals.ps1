# run-evals.ps1 — 端到端回归测试入口 (Windows PowerShell)
#
# 用法:
#   pwsh scripts/run-evals.ps1          # 完整运行
#   pwsh scripts/run-evals.ps1 -Quick   # 跳过单元测试
#
# 退出码:
#   0 = 全部通过
#   1 = 有失败

param(
    [switch]$Quick
)

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoDir = Split-Path -Parent $ScriptDir

$PassCount = 0
$FailCount = 0
$SkipCount = 0

function Pass($msg) {
    $script:PassCount++
    Write-Host "  ✅ $msg" -ForegroundColor Green
}

function Fail($msg) {
    $script:FailCount++
    Write-Host "  ❌ $msg" -ForegroundColor Red
}

function Skip($msg) {
    $script:SkipCount++
    Write-Host "  ⏭️  $msg" -ForegroundColor Yellow
}

Write-Host "========================================="
Write-Host " QGW 端到端回归测试"
Write-Host "========================================="
Write-Host ""

# ===== Phase 1: Python 单元测试 =====
Write-Host "📋 Phase 1: Python 单元测试"
Write-Host "-----------------------------------------"

$py = $null
try { $py = Get-Command python3 -ErrorAction Stop } catch {}
if (-not $py) { try { $py = Get-Command python -ErrorAction Stop } catch {} }

if ($py -and -not $Quick) {
    try {
        $pytestVersion = & $py.Source -m pytest --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  运行 gate-enforcer.py 测试..."
            Push-Location "$RepoDir\skills\quality-gate-workflow\scripts"
            & $py.Source -m pytest tests/ -v --tb=short 2>&1
            if ($LASTEXITCODE -eq 0) {
                Pass "gate-enforcer.py 单元测试全部通过"
            } else {
                Fail "gate-enforcer.py 单元测试有失败"
            }
            Pop-Location
        } else {
            Skip "pytest 未安装"
        }
    } catch {
        Skip "pytest 不可用"
    }
} elseif (-not $py) {
    Skip "Python 不可用"
}

Write-Host ""

# ===== Phase 2: CLI 冒烟测试 =====
Write-Host "📋 Phase 2: gate-enforcer.py CLI 冒烟测试"
Write-Host "-----------------------------------------"

if ($py) {
    $enforcer = "$RepoDir\skills\quality-gate-workflow\scripts\gate-enforcer.py"
    $tmpDir = Join-Path $env:TEMP "qgw-eval-$(Get-Random)"
    New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null
    New-Item -ItemType Directory -Path "$tmpDir\docs\plans" -Force | Out-Null
    New-Item -ItemType Directory -Path "$tmpDir\docs\verification" -Force | Out-Null
    New-Item -ItemType Directory -Path "$tmpDir\docs\reports" -Force | Out-Null
    New-Item -ItemType Directory -Path "$tmpDir\docs\sessions" -Force | Out-Null

    Push-Location $tmpDir

    # init
    & $py.Source $enforcer init --gate gate1 --mode prd 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Pass "init --gate gate1 成功" } else { Fail "init --gate gate1 失败" }

    # status
    & $py.Source $enforcer status 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Pass "status 查询成功" } else { Fail "status 查询失败" }

    # enter P0
    $result = & $py.Source $enforcer enter P0 2>&1
    if ($result -match "ALLOW") { Pass "enter P0 返回 ALLOW" } else { Fail "enter P0 未返回 ALLOW" }

    # complete P0
    $result = & $py.Source $enforcer complete P0 2>&1
    if ($result -match "OK") { Pass "complete P0 返回 OK" } else { Fail "complete P0 未返回 OK" }

    # self-check
    & $py.Source $enforcer self-check 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Pass "self-check 成功" } else { Fail "self-check 失败" }

    # prd-changed
    & $py.Source $enforcer prd-changed --impact cosmetic 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) { Pass "prd-changed --impact cosmetic 成功" } else { Fail "prd-changed 失败" }

    Pop-Location
    Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue
} else {
    Skip "Python 不可用，跳过 CLI 冒烟测试"
}

Write-Host ""

# ===== Phase 3: Shell 脚本语法检查 =====
Write-Host "📋 Phase 3: PowerShell 脚本语法检查"
Write-Host "-----------------------------------------"

$psFiles = Get-ChildItem -Path "$RepoDir\scripts" -Filter "*.ps1" -ErrorAction SilentlyContinue
foreach ($f in $psFiles) {
    try {
        $null = [System.Management.Automation.Language.Parser]::ParseFile($f.FullName, [ref]$null, [ref]$errors)
        if ($errors.Count -eq 0) {
            Pass "$($f.Name) 语法正确"
        } else {
            Fail "$($f.Name) 语法错误: $($errors[0].Message)"
        }
    } catch {
        Skip "$($f.Name) 无法解析"
    }
}

Write-Host ""

# ===== Phase 4: JSON 格式验证 =====
Write-Host "📋 Phase 4: JSON 格式验证"
Write-Host "-----------------------------------------"

$jsonFiles = Get-ChildItem -Path $RepoDir -Filter "*.json" -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -notmatch 'node_modules|\.git' }
$jsonErrors = 0
foreach ($jf in $jsonFiles) {
    try {
        $null = Get-Content $jf.FullName -Raw | ConvertFrom-Json
    } catch {
        Fail "$($jf.Name) JSON 格式无效"
        $jsonErrors++
    }
}
if ($jsonErrors -eq 0) { Pass "所有 JSON 文件格式有效 ($($jsonFiles.Count) 个文件)" }

Write-Host ""

# ===== 汇总 =====
Write-Host "========================================="
$total = $PassCount + $FailCount + $SkipCount
Write-Host " 📊 总计: $total | ✅ 通过: $PassCount | ❌ 失败: $FailCount | ⏭️  跳过: $SkipCount"
Write-Host "========================================="

if ($FailCount -gt 0) {
    Write-Host "回归测试失败 ($FailCount 项)" -ForegroundColor Red
    exit 1
} else {
    Write-Host "回归测试全部通过" -ForegroundColor Green
    exit 0
}

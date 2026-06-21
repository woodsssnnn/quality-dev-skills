# validate-all.ps1 — 全量验证脚本
param()
$repo = Split-Path -Parent $PSScriptRoot
$pass = 0; $fail = 0; $warn = 0

# Python 检测（兼容 python3 / python / py）
$py = $null
foreach ($c in @("python3", "python", "py")) {
    $cmd = Get-Command $c -ErrorAction SilentlyContinue
    if ($cmd) {
        $ver = & $cmd -c "import sys; print(sys.version_info[0])" 2>$null
        if ($ver -eq "3") { $py = $cmd.Source; break }
    }
}
if (-not $py) {
    Write-Host "ERROR: Python 3 not found (python3/python/py)" -ForegroundColor Red
    exit 1
}

function Pass($msg) { $script:pass++; Write-Host "  PASS $msg" -ForegroundColor Green }
function Fail($msg) { $script:fail++; Write-Host "  FAIL $msg" -ForegroundColor Red }
function Warn($msg) { $script:warn++; Write-Host "  WARN $msg" -ForegroundColor Yellow }

# ===== 1. JSON Validation =====
Write-Host "`n=== 1. JSON 格式验证 ==="
Get-ChildItem -Path $repo -Filter "*.json" -Recurse |
    Where-Object { $_.FullName -notmatch 'node_modules|\.git|\.pytest_cache|__pycache__' } |
    ForEach-Object {
        try {
            $null = Get-Content $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            Pass "$($_.FullName.Replace($repo + '\', ''))"
        } catch {
            Fail "$($_.FullName.Replace($repo + '\', '')): $($_.Exception.Message)"
        }
    }

# ===== 2. Python Syntax Check =====
Write-Host "`n=== 2. Python 语法校验 ==="
Get-ChildItem -Path $repo -Filter "*.py" -Recurse |
    Where-Object { $_.FullName -notmatch '__pycache__|\.pytest_cache' } |
    ForEach-Object {
        $r = & $py -m py_compile $_.FullName 2>&1
        if ($LASTEXITCODE -eq 0) {
            Pass "$($_.FullName.Replace($repo + '\', ''))"
        } else {
            Fail "$($_.FullName.Replace($repo + '\', '')): $r"
        }
    }

# ===== 3. SKILL.md Route Reference Integrity =====
Write-Host "`n=== 3. SKILL.md 路由引用完整性 ==="
$skillMd = Get-Content "$repo\skills\quality-gate-workflow\SKILL.md" -Raw
$refMatches = [regex]::Matches($skillMd, 'references/([\w\-\.]+\.md)')
$refDir = "$repo\skills\quality-gate-workflow\references"
$checked = @{}
foreach ($m in $refMatches) {
    $fname = $m.Groups[1].Value
    if ($checked[$fname]) { continue }
    $checked[$fname] = $true
    $fpath = Join-Path $refDir $fname
    if (Test-Path $fpath) {
        Pass "reference/$fname exists"
    } else {
        Fail "reference/$fname MISSING (referenced in SKILL.md)"
    }
}

# ===== 4. New Skill Package Structure =====
Write-Host "`n=== 4. 技能包结构完整性 ==="
$skills = @(
    @{name="qgw-init"; required=@("SKILL.md","scripts\qgw-init.sh","references\platform-configs.md","references\workflow-modes.md","CHANGELOG.md")},
    @{name="api-design-review"; required=@("SKILL.md","references\api-conventions.md","scripts\check-api-convention.py","evaluations","manifest-entry.json","CHANGELOG.md")},
    @{name="db-migration-gate"; required=@("SKILL.md","references\migration-conventions.md","scripts\check-migration-safety.py","evaluations","manifest-entry.json","CHANGELOG.md")}
)
foreach ($skill in $skills) {
    $skillDir = "$repo\skills\$($skill.name)"
    if (Test-Path $skillDir) {
        Pass "skills/$($skill.name)/ directory exists"
        foreach ($req in $skill.required) {
            $path = Join-Path $skillDir $req
            if (Test-Path $path) {
                Pass "  $req"
            } else {
                Fail "  $req MISSING"
            }
        }
    } else {
        Fail "skills/$($skill.name)/ directory MISSING"
    }
}

# ===== 5. Version Consistency =====
Write-Host "`n=== 5. 版本号一致性 ==="
$vj = Get-Content "$repo\version.json" -Raw | ConvertFrom-Json
$vjVer = $vj.skills.'quality-gate-workflow'.version
$skillVer = (Select-String -Path "$repo\skills\quality-gate-workflow\SKILL.md" -Pattern "version:\s*(\S+)" | Select-Object -First 1).Matches[0].Groups[1].Value
if ($vjVer -eq $skillVer) {
    Pass "version.json ($vjVer) matches SKILL.md ($skillVer)"
} else {
    Fail "version.json ($vjVer) != SKILL.md ($skillVer)"
}

$optVer = (Select-String -Path "$repo\skills\skill-optimizer\SKILL.md" -Pattern "version:\s*(\S+)" | Select-Object -First 1).Matches[0].Groups[1].Value
$vjOptVer = $vj.skills.'skill-optimizer'.version
if ($vjOptVer -eq $optVer) {
    Pass "version.json ($vjOptVer) matches skill-optimizer ($optVer)"
} else {
    Fail "version.json ($vjOptVer) != skill-optimizer ($optVer)"
}

# ===== 6. CI/CD Files =====
Write-Host "`n=== 6. CI/CD 文件完整性 ==="
$ciFiles = @(
    ".github\workflows\quality-check.yml",
    ".github\workflows\release.yml",
    ".github\workflows\qgw-pr-check.yml",
    "scripts\qgw-pr-check.sh",
    "scripts\run-evals.sh",
    "scripts\run-evals.ps1"
)
foreach ($f in $ciFiles) {
    if (Test-Path "$repo\$f") { Pass $f } else { Fail "$f MISSING" }
}

# ===== 7. Manifest Files =====
Write-Host "`n=== 7. Manifest 文件 ==="
$manifestFiles = @(
    "skill-manifest.json",
    "shared\skill-manifest-schema.json",
    "shared\skill-protocol.md",
    "shared\vertical-skill-guide.md",
    "scripts\generate-manifest.py"
)
foreach ($f in $manifestFiles) {
    if (Test-Path "$repo\$f") { Pass $f } else { Fail "$f MISSING" }
}

# ===== Summary =====
Write-Host "`n========================================="
Write-Host " Total: $($pass+$fail+$warn) | PASS: $pass | FAIL: $fail | WARN: $warn"
Write-Host "========================================="
if ($fail -gt 0) { exit 1 } else { exit 0 }

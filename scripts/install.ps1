# install.ps1 — quality-dev-skills Windows PowerShell 安装脚本
#
# 用途：install.sh 的 Windows 原生替代。在 bash（Git Bash/MSYS2）不可用时使用。
#
# 用法：
#   .\scripts\install.ps1                          # 安装全部到 $env:USERPROFILE\.agents\skills
#   .\scripts\install.ps1 -Skill quality-gate-workflow    # 安装单个
#   .\scripts\install.ps1 -Update                  # 更新（重新链接）
#   .\scripts\install.ps1 -Init                    # 一键安装：链接 + 工作区初始化 + 健康检查
#   .\scripts\install.ps1 -DryRun                  # 预览安装动作，不执行
#
# 来源目录不绑定：git clone 到任意位置，在该目录下运行本脚本即可全局安装。
# 脚本基于自身位置自动定位源目录（$RepoDir\skills\）。
#
# 链接策略（按优先级降级）：
#   1) Symlink (SymbolicLink)        — 需管理员或开发者模式
#   2) Junction (New-Item -ItemType Junction) — 任意用户，跨卷可用，对目录与 symlink 等价
#   3) Copy (Copy-Item -Recurse)     — 兜底，源修改不会同步
#
# 注意：Junction 对目录类型不需要任何特权（与 SymbolicLink 不同），是 Win10/11
# 上 Git Bash `ln -s` 实际创建的同类对象。下游脚本应以"读 reparse point"方式
# 安全处理，例如 deploy.sh 中用 `pwd -P` 获取物理路径。

param(
    [string[]]$Skill = @(),
    [switch]$Update = $false,
    [switch]$Init = $false,
    [switch]$DryRun = $false,
    [switch]$Help = $false
)

if ($Help) {
    Write-Host "Usage: .\scripts\install.ps1 [[-Skill] <string[]>] [-Update] [-Init] [-DryRun]"
    Write-Host "  -Skill    Skill name, e.g. quality-gate-workflow, skill-optimizer"
    Write-Host "  -Update   Update existing links (re-establish)"
    Write-Host "  -Init     Full setup: link + workspace init + health check"
    Write-Host "  -DryRun   Preview actions without executing"
    Write-Host "  Target:   $env:USERPROFILE\.agents\skills"
    exit 0
}

$RepoDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SkillsSrc = Join-Path $RepoDir "skills"

# 目标目录：统一全局安装到 $env:USERPROFILE\.agents\skills
$TargetDirs = @("$env:USERPROFILE\.agents\skills")

# 探测链接能力
function Test-LinkCapability {
    param([string]$Kind)  # "SymbolicLink" or "Junction"
    $link = Join-Path $env:TEMP ("_qds_probe_{0}_{1}" -f $Kind, [Guid]::NewGuid())
    $tgt  = Join-Path $env:TEMP ("_qds_probe_tgt_{0}" -f [Guid]::NewGuid())
    try {
        New-Item -ItemType Directory -Path $tgt -Force | Out-Null
        New-Item -ItemType $Kind -Path $link -Target $tgt -Force | Out-Null
        $ok = (Get-Item $link).Attributes.HasFlag([IO.FileAttributes]::ReparsePoint)
        Remove-Item $link -Force -ErrorAction SilentlyContinue
        Remove-Item $tgt  -Force -ErrorAction SilentlyContinue
        return $ok
    } catch {
        Remove-Item $link -Force -ErrorAction SilentlyContinue
        Remove-Item $tgt  -Force -ErrorAction SilentlyContinue
        return $false
    }
}

$CanSymlink  = Test-LinkCapability -Kind "SymbolicLink"
$CanJunction = Test-LinkCapability -Kind "Junction"

if (-not $CanSymlink -and -not $CanJunction) {
    Write-Host "[install] WARNING: no reparse point capability. Falling back to copy mode." -ForegroundColor Yellow
    Write-Host "  Source edits will NOT propagate. Enable developer mode or run as admin for live link." -ForegroundColor Yellow
}

function Remove-SkillLink {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    $item = Get-Item $Path -Force -ErrorAction SilentlyContinue
    if ($null -ne $item -and $item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        # Junction / symlink: never recurse, just drop the link
        cmd.exe /c "rmdir `"$Path`"" 2>&1 | Out-Null
        if (Test-Path $Path) {
            Remove-Item $Path -Force -ErrorAction SilentlyContinue
        }
    } else {
        Remove-Item $Path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function New-SkillLink {
    param([string]$Link, [string]$Target, [bool]$UseSymlink, [bool]$UseJunction)
    $parent = Split-Path -Parent $Link
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    Remove-SkillLink -Path $Link

    if ($UseSymlink) {
        New-Item -ItemType SymbolicLink -Path $Link -Target $Target -Force | Out-Null
        return "symlink"
    } elseif ($UseJunction) {
        New-Item -ItemType Junction -Path $Link -Target $Target -Force | Out-Null
        return "junction"
    } else {
        Copy-Item -Path $Target -Destination $Link -Recurse -Force
        return "copy"
    }
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " quality-dev-skills install (PowerShell)" -ForegroundColor Cyan
Write-Host "  symlink=$CanSymlink  junction=$CanJunction  scope=global" -ForegroundColor DarkGray
Write-Host "========================================="
Write-Host ""

# --DryRun 模式：预览但不执行
if ($DryRun) {
    Write-Host "[install] DRY RUN — no changes will be made" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "[install] Would link skills to: $env:USERPROFILE\.agents\skills"
    $skillNames = if ($Skill.Count -gt 0) { $Skill -join ", " } else { "all" }
    Write-Host "[install] Skills to install: $skillNames"
    if ($Init) {
        Write-Host "[install] Would initialize workspace: docs/{plans,verification,reports,sessions}"
        Write-Host "[install] Would run health check"
    }
    Write-Host ""
    Write-Host "[install] Run without -DryRun to apply." -ForegroundColor Yellow
    exit 0
}

$report = @()
$skillsToInstall = if ($Skill.Count -gt 0) { $Skill } else {
    Get-ChildItem -Path $SkillsSrc -Directory | ForEach-Object { $_.Name }
}

foreach ($s in $skillsToInstall) {
    $src = Join-Path $SkillsSrc $s
    if (-not (Test-Path (Join-Path $src "SKILL.md"))) {
        Write-Host "[install] SKIP $s : SKILL.md missing" -ForegroundColor Red
        continue
    }

    foreach ($destRoot in $TargetDirs) {
        $dest = Join-Path $destRoot $s
        try {
            $mode = New-SkillLink -Link $dest -Target $src -UseSymlink $CanSymlink -UseJunction $CanJunction
            $hasMd = Test-Path (Join-Path $dest "SKILL.md")
            $report += [PSCustomObject]@{
                Skill    = $s
                Target   = $dest
                Mode     = $mode
                SKILL_md = $hasMd
            }
        } catch {
            $report += [PSCustomObject]@{
                Skill    = $s
                Target   = $dest
                Mode     = "FAILED"
                SKILL_md = $false
            }
            Write-Host "[install] FAIL $s -> $dest : $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Install result" -ForegroundColor Cyan
Write-Host "========================================="
$report | Format-Table -AutoSize | Out-String | Write-Host

# --Init 模式：额外执行工作区初始化
if ($Init) {
    Write-Host "" -ForegroundColor Cyan
    Write-Host "[install] Initializing workspace..." -ForegroundColor Cyan

    $workspaceDirs = @("docs\plans", "docs\verification", "docs\reports", "docs\sessions")
    foreach ($dir in $workspaceDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "[install]   Created: $dir" -ForegroundColor Green
        } else {
            Write-Host "[install]   Exists: $dir" -ForegroundColor DarkGray
        }
    }

    $healthCheck = Join-Path $RepoDir "skills\quality-gate-workflow\scripts\health-check.sh"
    if (Test-Path $healthCheck) {
        Write-Host "" -ForegroundColor Cyan
        Write-Host "[install] Running health check..." -ForegroundColor Cyan
        try { bash $healthCheck } catch {
            Write-Host "[install] Health check completed with warnings" -ForegroundColor Yellow
        }
    }
}

# --DryRun 模式已在上方处理，此处正常结束输出
if (-not $DryRun) {
    Write-Host ""
    Write-Host " Next steps:" -ForegroundColor Green
    Write-Host "   1. 在项目根目录创建 .qgw/ 目录（可选，用于项目定制）" -ForegroundColor Gray
    Write-Host "   2. 在 AI 对话中说`"帮我实现这个需求`"开始使用" -ForegroundColor Gray
    Write-Host "   3. 或使用 --preset feature 启动完整流程" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Update: re-run install.ps1 after git pull" -ForegroundColor Gray
Write-Host "Uninstall: bash scripts/uninstall.sh  (or remove dirs manually)" -ForegroundColor Gray

[CmdletBinding()]
param(
    [switch]$Check,
    [string[]]$Project
)

$arguments = @("$PSScriptRoot\sync_docs.py")
if ($Check) {
    $arguments += "--check"
}
foreach ($projectId in $Project) {
    $arguments += @("--project", $projectId)
}

& python @arguments
exit $LASTEXITCODE


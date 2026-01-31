# ZORK RPG - Speaking SSH Client
# Connects to SSH server and speaks text locally!
# Run this on YOUR machine (the client)

param(
    [string]$Server = "localhost",
    [int]$Port = 2222,
    [string]$Username = "player",
    [switch]$NoVoice
)

Write-Host @"
╔════════════════════════════════════════════════╗
║   ZORK RPG - SSH CLIENT WITH LOCAL VOICE      ║
║        🔊 Voice plays on YOUR speakers!       ║
╚════════════════════════════════════════════════╝
"@

if (-not $NoVoice) {
    Write-Host "🔊 Local voice synthesis ENABLED!"
    Write-Host "   (Use -NoVoice to disable)"
} else {
    Write-Host "🔇 Voice synthesis disabled"
}

Write-Host ""
Write-Host "Connecting to $Server`:$Port as $Username..."
Write-Host "Press Ctrl+C to disconnect"
Write-Host ""

# Speech synthesizer setup
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 0
$synth.Volume = 85

# Voice rate settings for different types
$voiceRates = @{
    'narrator' = 0
    'troll' = -2
    'goblin' = 3
    'dragon' = -4
    'merchant' = 1
}

function Speak-Text {
    param(
        [string]$Text,
        [string]$VoiceType = "narrator"
    )
    
    if ($NoVoice) { return }
    
    # Clean text for speech
    $cleanText = $Text -replace '\[█░\]+\]', ''  # Remove health bars
    $cleanText = $cleanText -replace '[⚔️🔥💀👤🕊️⚠️💬💨👋✅❌📊💰🚨]', ''  # Remove emoji
    $cleanText = $cleanText -replace '\x1b\[[0-9;]*m', ''  # Remove ANSI codes
    $cleanText = $cleanText -replace '>\s*$', ''  # Remove prompts
    $cleanText = $cleanText.Trim()
    
    if ($cleanText.Length -eq 0) { return }
    
    # Set voice rate based on type
    if ($voiceRates.ContainsKey($VoiceType)) {
        $synth.Rate = $voiceRates[$VoiceType]
    } else {
        $synth.Rate = 0
    }
    
    # Speak asynchronously (non-blocking)
    try {
        $synth.SpeakAsync($cleanText) | Out-Null
    } catch {
        # Ignore errors
    }
}

function Get-VoiceType {
    param([string]$Text)
    
    $lower = $Text.ToLower()
    
    if ($lower -match 'troll.*(?:says|roars|attacks)') { return 'troll' }
    if ($lower -match 'goblin.*(?:says|attacks)') { return 'goblin' }
    if ($lower -match 'dragon.*(?:says|roars|attacks)') { return 'dragon' }
    if ($lower -match 'merchant.*says') { return 'merchant' }
    
    return 'narrator'
}

# Create SSH process
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "ssh"
$psi.Arguments = "-p $Port $Username@$Server"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardInput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $false

try {
    $process = [System.Diagnostics.Process]::Start($psi)
    
    # Background job to read SSH output and speak it
    $readerJob = Start-Job -ScriptBlock {
        param($process, $NoVoice)
        
        # Recreate synth in job
        Add-Type -AssemblyName System.Speech
        $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
        
        $voiceRates = @{
            'narrator' = 0
            'troll' = -2
            'goblin' = 3
            'dragon' = -4
            'merchant' = 1
        }
        
        function Get-VoiceType {
            param([string]$Text)
            $lower = $Text.ToLower()
            if ($lower -match 'troll.*(?:says|roars|attacks)') { return 'troll' }
            if ($lower -match 'goblin.*(?:says|attacks)') { return 'goblin' }
            if ($lower -match 'dragon.*(?:says|roars|attacks)') { return 'dragon' }
            if ($lower -match 'merchant.*says') { return 'merchant' }
            return 'narrator'
        }
        
        while (-not $process.HasExited) {
            $line = $process.StandardOutput.ReadLine()
            if ($line) {
                Write-Output $line
                
                if (-not $NoVoice) {
                    # Determine voice type and speak
                    $voiceType = Get-VoiceType $line
                    
                    # Clean text
                    $cleanText = $line -replace '\[█░\]+\]', ''
                    $cleanText = $cleanText -replace '[⚔️🔥💀👤🕊️⚠️💬💨👋✅❌📊💰🚨]', ''
                    $cleanText = $cleanText -replace '>\s*$', ''
                    $cleanText = $cleanText.Trim()
                    
                    if ($cleanText.Length -gt 5) {
                        if ($voiceRates.ContainsKey($voiceType)) {
                            $synth.Rate = $voiceRates[$voiceType]
                        }
                        try {
                            $synth.SpeakAsync($cleanText) | Out-Null
                        } catch {}
                    }
                }
            }
        }
    } -ArgumentList $process, $NoVoice
    
    # Main loop - read user input and send to SSH
    Write-Host "Connected! Type commands..."
    
    while (-not $process.HasExited) {
        # Show output from SSH
        if ($readerJob.HasMoreData) {
            Receive-Job $readerJob | Write-Host
        }
        
        # Check for user input (non-blocking)
        if ([Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            
            if ($key.Key -eq 'C' -and $key.Modifiers -eq 'Control') {
                Write-Host "`nDisconnecting..."
                break
            }
            
            # Echo character
            Write-Host -NoNewline $key.KeyChar
            
            # Send to SSH
            $process.StandardInput.Write($key.KeyChar)
            
            # If Enter, flush
            if ($key.Key -eq 'Enter') {
                $process.StandardInput.WriteLine()
                Write-Host ""
            }
        }
        
        Start-Sleep -Milliseconds 50
    }
    
    # Cleanup
    Stop-Job $readerJob -ErrorAction SilentlyContinue
    Remove-Job $readerJob -ErrorAction SilentlyContinue
    
    if (-not $process.HasExited) {
        $process.Kill()
    }
    
    $process.Dispose()
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
} finally {
    Write-Host "`nDisconnected."
}

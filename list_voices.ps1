Add-Type -AssemblyName System.Speech
$v = (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices()
foreach ($x in $v) { Write-Output ($x.VoiceInfo.Name + " | " + $x.VoiceInfo.Culture) }

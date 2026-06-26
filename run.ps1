# Run the full Regulatory Radar pipeline with Twilio credentials
# Usage: .\run.ps1

$env:TWILIO_ACCOUNT_SID = 'AC8be527804c7ea9fff19a401a06c53f44'
$env:TWILIO_AUTH_TOKEN  = 'dd9d0ae6e6b8b3b6866504066ebd08b0'
$env:TWILIO_FROM        = '+19516418619'
$env:TWILIO_TO_TEST     = '+491758847709'

python main.py

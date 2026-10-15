# Run the full Regulatory Radar pipeline with Twilio credentials
# Usage: .\run.ps1

$env:TWILIO_ACCOUNT_SID = 'your_account_sid_here'
$env:TWILIO_AUTH_TOKEN  = 'your_auth_token_here'
$env:TWILIO_FROM        = 'your_twilio_phone_number'
$env:TWILIO_TO_TEST     = 'your_test_phone_number'

python main.py

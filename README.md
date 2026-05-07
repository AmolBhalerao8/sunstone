# ZOL AI Voice Receptionist

AI phone receptionist and service quoting assistant for ZOL, a mechanic shop.

Built with:

- **Vapi** for the live voice agent and phone number
- **Vapi Native Google Calendar** for availability checks and appointment booking
- **FastAPI** for tool webhook endpoints
- **Twilio SMS** for quote and follow-up text messages

## How It Works

1. A customer calls the Vapi phone number.
2. The AI receptionist answers common shop questions and collects the minimum repair/service details.
3. The assistant confirms the caller's phone number from caller ID, or asks for the best SMS number if needed.
4. Vapi checks the shop calendar for available drop-off or inspection times.
5. The backend calculates an estimate and sends the quote by SMS to the caller's phone number.
6. If the customer chooses a time, Vapi books the appointment on Google Calendar.
7. The backend sends a follow-up SMS with the confirmed appointment details.

## Project Structure

```text
sunstone/
├── backend/
│   ├── main.py
│   ├── keepalive.py
│   ├── routes/
│   │   ├── health.py
│   │   └── tools.py
│   ├── models/
│   │   ├── lead.py
│   │   ├── quote.py
│   │   ├── service_info.py
│   │   └── tool_schemas.py
│   ├── services/
│   │   ├── pricing.py
│   │   └── sms_service.py
│   ├── .env.example
│   ├── Procfile
│   └── requirements.txt
├── vapi/
│   ├── agent_config.json
│   └── README_vapi_setup.md
├── render.yaml
├── railway.toml
└── README.md
```

## Quick Start

```bash
cd sunstone/backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

Expose the backend with ngrok for Vapi testing:

```bash
ngrok http 8000
```

Set `BASE_URL` in `.env` to the public HTTPS URL.

## Environment Variables

| Variable | Description |
|---|---|
| `TWILIO_ACCOUNT_SID` | Twilio account SID |
| `TWILIO_AUTH_TOKEN` | Twilio auth token |
| `TWILIO_FROM_NUMBER` | Twilio phone number used for outbound SMS |
| `SHOP_NAME` | Shop display name |
| `SHOP_PHONE` | Public shop phone |
| `SHOP_ADDRESS` | Shop address |
| `SHOP_WEBSITE` | Shop website |
| `SHOP_HOURS` | Business hours shown in texts and assistant answers |
| `BASE_URL` | Public URL for Vapi webhooks |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/tools/send_quote_sms` | Calculate estimate and send SMS quote |
| `POST` | `/tools/send_followup_sms` | Send appointment or callback follow-up SMS |

## Pricing

Pricing lives in `backend/services/pricing.py`. The quote is an estimate, not a final invoice. The assistant should explain that final pricing depends on inspection, parts availability, vehicle condition, and taxes/fees.

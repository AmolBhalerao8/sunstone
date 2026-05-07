# Vapi + ZOL Setup Guide

This setup uses Vapi for phone calls, Vapi's native Google Calendar tools for appointment scheduling, and the ZOL FastAPI backend for SMS quote/follow-up tools.

## 1. Configure Twilio

1. Create or log in to a Twilio account.
2. Select the ZOL Twilio SMS number: `(878) 673-0209`.
3. Copy:
   - Account SID
   - Auth Token
   - Twilio phone number
4. Add them to `sunstone/backend/.env` or your hosting provider:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_FROM_NUMBER=+18786730209
SHOP_TEAM_NOTIFY_NUMBER=
```

Find the Account SID/Auth Token in Twilio at **Console -> Account Dashboard -> Account Info**. The Account SID starts with `AC...`; click **Show** next to Auth Token to reveal it.

## 2. Run The Backend

```bash
cd sunstone/backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` and confirm the API starts.

Expose the backend for Vapi:

```bash
ngrok http 8000
```

Set `BASE_URL` in `.env` to the ngrok HTTPS URL, then restart the backend.

## 3. Connect Google Calendar In Vapi

1. Log in to [Vapi](https://vapi.ai).
2. Go to **Integrations -> Tools Provider -> Google Calendar**.
3. Connect `ezaz@scopiclegal.com`, which owns the ZOL appointment calendar.

## 4. Create The Assistant

1. Go to **Assistants -> Create Assistant -> Blank**.
2. Open the JSON editor.
3. Paste `sunstone/vapi/agent_config.json`.
4. Replace `{{BASE_URL}}` with your deployed backend URL.
5. Save.

The assistant should show four tools:

- `checkAvailability`
- `createEvent`
- `send_quote_sms`
- `send_followup_sms`

## 5. Attach A Phone Number

1. In Vapi, go to **Phone Numbers**.
2. Buy or connect a phone number.
3. Assign the number to the ZOL assistant.
4. Call the number and test the full flow.

## Testing Checklist

- [ ] `GET /health` returns `status: ok`
- [ ] Assistant answers common shop questions
- [ ] Assistant confirms caller phone number and SMS consent
- [ ] `send_quote_sms` sends the quote text
- [ ] Calendar availability is read back clearly
- [ ] `createEvent` creates a calendar event after customer consent
- [ ] `send_followup_sms` sends appointment confirmation
- [ ] If `SHOP_TEAM_NOTIFY_NUMBER` is set, the ZOL team receives a booking notification

## Pricing Adjustments

Edit `sunstone/backend/services/pricing.py` to change:

- Base rates by service type
- Add-on rates
- OEM or budget parts estimate multipliers
- Older/high-mileage vehicle allowances

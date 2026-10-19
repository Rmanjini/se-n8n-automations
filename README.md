# Social Eagle — n8n Automations

Sanitized exports of Social Eagle's n8n workflows (backup of 28 May 2026). Import any file in `workflows/` into n8n via **Workflows → Import from File**.

| Workflow | What it does |
|---|---|
| `kylas-self-form-lead-import.json` | Website self-form webhook → Kylas lead + Google Sheet log |
| `social-eagle-form-kylas-crm-final-working.json` | Social Eagle form → Kylas CRM lead |
| `social-eagle-lead-import-sheet-kylas.json` | Google Sheet lead import → Kylas |
| `webinar-nurturing.json` | Webinar registrations → Sheets, day-based nurture schedule |
| `callzyer-to-kylas.json` | Callyzer call logs/recordings → Kylas leads, call logs, notes |
| `orufy-forms-to-kylas.json` | Orufy bookings/forms → Kylas leads, meetings, OpenAI summaries |
| `post-meeting-dm-kylas-n8n-dt.json` | Kylas meeting webhook → timed post-meeting DMs |
| `social-eagle-n8n-workflow.json` | AI voice caller: Exotel + Sarvam STT/TTS + GPT-4o-mini |

## What was removed

All API keys, credential IDs, webhook IDs/URLs, n8n host names, Google Sheet / Apps Script IDs, Zoom links, emails, phone numbers and saved test data (`pinData`) are stripped or replaced with placeholders like `YOUR_API_KEY`, `YOUR_SHEET_ID`, `user@example.com`, `+910000000000`.

## Setup after import

1. Create your own credentials in n8n (Kylas header auth `api-key`, Google Sheets OAuth2, OpenAI) and select them on each node.
2. Replace every `YOUR_…` placeholder and the phone/email → owner mapping tables in the Code nodes.
3. Set env vars where referenced: `OPENAI_API_KEY`, `SARVAM_API_KEY`, `EXOTEL_SID`, `EXOTEL_SMS_SENDER_ID`, `N8N_WEBHOOK_BASE_URL`.

## Re-sanitizing new exports

```bash
python3 sanitize.py "<folder with raw exports>" workflows
```
Always grep the output for your real keys before committing.

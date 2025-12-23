# Stripe top-up (10p → 50 credits) setup

This project supports Stripe Checkout for the existing “Top Up 10p → 50 Credits” button.

## 1) IMPORTANT: use TEST mode keys
Do **not** use live keys during setup/testing.

If you accidentally shared or pasted live keys anywhere, rotate them in Stripe Dashboard immediately.

## 2) Add these to `.env`
Set these values (TEST MODE):

- `STRIPE_SECRET_KEY=sk_test_...`
- `STRIPE_WEBHOOK_SECRET=whsec_...`

Notes:
- `STRIPE_PUBLISHABLE_KEY` is **not required** for the current server-driven Checkout flow.
- When `STRIPE_SECRET_KEY` is present, the backend will automatically use Stripe for `/api/create-checkout`.

## 3) Configure your Stripe webhook
Create a webhook endpoint in Stripe Dashboard (Test mode):

- Endpoint URL: `https://<your-public-url>/api/webhooks/stripe`
- Events to send: `checkout.session.completed`

Copy the signing secret and set it as `STRIPE_WEBHOOK_SECRET`.

## 4) What the code does
- POST `/api/create-checkout` creates a Stripe Checkout Session for **GBP £0.10** and redirects back to:
  - success: `/admin.html?topup=success`
  - cancel: `/admin.html?topup=cancel`
- POST `/api/webhooks/stripe` verifies the Stripe signature and, on `checkout.session.completed`, credits:
  - `account_settings.minutes_remaining += 50`
  - `account_settings.total_minutes_purchased += 50`

## 5) Quick verification
1. Start the server.
2. Click Top Up.
3. Use a Stripe test card (e.g. `4242 4242 4242 4242`).
4. Ensure the webhook delivers `checkout.session.completed`.
5. Return to `/admin.html?topup=success` and credits should refresh.

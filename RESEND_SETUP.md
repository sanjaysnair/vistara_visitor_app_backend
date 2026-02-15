# Email Setup with Resend

The application now uses **Resend** for email notifications instead of SMTP (which is blocked on Render).

## Setup Instructions

### 1. Get Resend API Key

1. Go to [resend.com](https://resend.com) and sign up for a free account
2. Navigate to **API Keys** in the dashboard
3. Click **Create API Key**
4. Copy the API key (starts with `re_`)

### 2. Verify Domain (Optional but Recommended)

For production use, verify your domain:

1. In Resend dashboard, go to **Domains**
2. Click **Add Domain** and enter your domain
3. Add the DNS records provided by Resend
4. Once verified, you can send from `noreply@yourdomain.com`

**For testing:** Use `onboarding@resend.dev` (default, works without domain verification)

### 3. Configure Environment Variables in Render

Add these environment variables to your Render service:

```
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=onboarding@resend.dev
ADMIN_EMAIL=getsanjaysnair@gmail.com
```

**Important:**
- Replace `RESEND_API_KEY` with your actual API key from step 1
- If you verified a domain, change `FROM_EMAIL` to `noreply@yourdomain.com`
- Keep `ADMIN_EMAIL` as your admin email address

### 4. Deploy

Commit and push the changes:

```bash
git add .
git commit -m "Switch from SMTP to Resend API for email"
git push
```

Render will automatically redeploy with the new configuration.

## Free Tier Limits

Resend free tier includes:
- ✅ 100 emails per day
- ✅ 1 verified domain
- ✅ Full API access

Upgrade to paid plan if you need more emails.

## Troubleshooting

### Email not sending?

1. Check Render logs for errors
2. Verify `RESEND_API_KEY` is set correctly
3. Check Resend dashboard for API usage and errors
4. Ensure `FROM_EMAIL` matches your verified domain (or use `onboarding@resend.dev`)

### Test the API

You can test email sending from Resend dashboard → **Emails** → **Send Test Email**

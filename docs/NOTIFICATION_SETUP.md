# Notification System Configuration

## Setup Instructions

### 1. Discord Configuration

Copy the template configuration file:
```bash
cp backend/data/notification_config.template.json backend/data/notification_config.json
```

Edit `backend/data/notification_config.json` and replace `YOUR_DISCORD_WEBHOOK_URL_HERE` with your actual Discord webhook URL.

### 2. Discord Webhook Setup

1. Go to your Discord server settings
2. Navigate to Integrations > Webhooks
3. Create a new webhook or use an existing one
4. Copy the webhook URL
5. Paste it into your `notification_config.json` file

### 3. Configuration Options

- **discord.webhook_url**: Your Discord webhook URL (required)
- **discord.enable_embeds**: Use rich embeds (recommended: true)
- **discord.enable_mentions**: Enable @everyone mentions (default: false)
- **discord.batch_size**: Number of notifications to batch together (default: 5)
- **rate_limiting.min_interval_minutes**: Minimum time between notifications (default: 5)
- **rate_limiting.max_per_hour**: Maximum notifications per hour (default: 12)
- **notifications.signal_threshold**: Minimum signal strength to notify (default: 7.0)
- **notifications.enable_error_alerts**: Send error notifications (default: true)
- **notifications.enable_daily_summary**: Send daily summaries (default: true)
- **notifications.daily_summary_time**: Time for daily summary in HH:MM format (default: "09:00")

### 4. Testing

The notification system includes comprehensive testing. Test files are located in `tests/feature_tests/` but are excluded from git by default to prevent accidental commits of test configurations.

### 5. Security Notes

- Never commit your actual Discord webhook URL to version control
- The `notification_config.json` file is automatically ignored by git
- Use the template file for sharing configuration structure

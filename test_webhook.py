from slack_sdk.webhook import WebhookClient

webhook_url = 'https://hooks.slack.com/services/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'
slack = WebhookClient(webhook_url)
response = slack.send(text="Test message from email tracker!")
print(response.status_code, response.body)

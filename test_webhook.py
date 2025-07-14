from slack_sdk.webhook import WebhookClient

webhook_url = 'https://hooks.slack.com/services/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'
slack = WebhookClient(webhook_url)
response = slack.send(text="Test message from email tracker!")
print(response.status_code, response.body)

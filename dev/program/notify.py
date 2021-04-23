from notifiers import get_notifier

class Notifier:
	def __init__(self, main):
		self.main = main
	

	def alert(self, message):
		print(message)
		p = get_notifier("pushover")
		p.notify(user=self.main.config.pushover_user, token=self.main.config.pushover_token, message=message)
class CaptchaGuess:
    def __init__(self, captcha_token, captchaObfuscationToken, action, guess):
        self.captcha_token = captcha_token
        self.captchaObfuscationToken = captchaObfuscationToken
        self.action = action
        self.guess = guess

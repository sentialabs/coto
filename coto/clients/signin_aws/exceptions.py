from .captcha_guess import CaptchaGuess

class CaptchaRequiredException(Exception):
    def __init__(self, CES, CaptchaURL, captchaObfuscationToken, action):
        super().__init__(
            "Captcha required for action: {}".format(action)
        )

        self.CES = CES
        self.CaptchaURL = CaptchaURL
        self.captchaObfuscationToken = captchaObfuscationToken
        self.action = action

    def guess(self, guess):
        return CaptchaGuess(
            self.CES,
            self.captchaObfuscationToken,
            self.action,
            guess,
        )
from io import BytesIO
from bs4 import BeautifulSoup
from pyotp import TOTP
from urllib import parse
import json
from . import BaseClient
from .signin_amazon import ap_url
import time
from PIL import Image
import shutil
import base64
import tempfile


class Client(BaseClient):
    REQUIRES_AUTHENTICATION = False
    __reset_page = None
    _REDIRECT_URL = "https://console.aws.amazon.com/console/home?state=hashArgs%23&isauthcode=true"

    def __init__(self, session):
        super().__init__(session)
        self.__csrf_token = None

    def _csrf_token(self):
        if self.__csrf_token == None:
            self._get_tokens()

        return self.__csrf_token

    def _get_tokens(self):
        r = self.session()._get(
            'https://signin.aws.amazon.com/resetpassword'
        )

        if r.status_code != 200:
            raise Exception("failed get tokens")

        soup = BeautifulSoup(r.text, 'html.parser')
        meta = {
            m['name']: m['content']
            for m in soup.find_all('meta') if 'name' in m.attrs
        }

        if not 'csrf_token' in meta:
            raise Exception("failed get csrf_token")
        self.__csrf_token = meta['csrf_token']

    def _action(self, action, data=None, api="signin"):
        """
        Execute an action on the signin API.

        Args:
            action: Action to execute.
            data: Arguments for the action.

        Returns:
            dict: Action response.
        """
        if not data:
            data = {}

        data['action'] = action
        # data['redirect_uri'] = self._REDIRECT_URL
        data['csrf'] = self._csrf_token()

        r = self.session()._post(
            "https://signin.aws.amazon.com/{0}".format(api),
            data=data,
        )

        if r.status_code != 200:
            print(r.text)
            raise Exception("failed action {0}".format(action))

        out = json.loads(r.text)
        if out['state'].lower() != 'success':
            if 'Message' in out['properties']:
                raise Exception("failed action {0}: {1}".format(action, out['properties']['Message']))
            else:
                raise Exception("failed action {0}".format(action))

        return out['properties']

    def reset_password(self, reset_token_url, password):
        """
        Performs a password reset.
        """
        query = parse.parse_qs(parse.urlparse(reset_token_url).query)
        return self._action('resetPasswordSubmitForm', {
            'token': query['token'][0],
            'key': query['key'][0],
            'newpassword': password,
            'confirmpassword': password,
        }, api='resetpassword')

    def request_otp_forgot_password(self, email):
        """
        Request an OTP to be sent to the email.
        """
        response = self.session()._get(ap_url(email, 'forgotpassword'))
        soup = BeautifulSoup(response.text, 'html.parser')

        error = soup.find(id="message_error")
        if error:
            message = error.get_text()
            # Enter the characters as they are given in the challenge.
            raise Exception(message)

        form = soup.find('form', id="ap_fpp_1a_form")

        data = {'metadata1': self.session()._metadata1_generator.generate()}

        for field in form.find_all('input'):
            name = field.get('name')
            if not name:
                continue
            value = field.get('value')
            data[name] = value
                
        data['email'] = email
        captcha_page = self.session()._post(
            form.get('action'),
            data=data
        )

        captcha_page_soup = BeautifulSoup(captcha_page.text, 'html.parser')
        div = captcha_page_soup.find_all('div', class_='cvf-captcha-img')
        solver = self.session()._captcha_solver

        tmp_folder = tempfile.TemporaryDirectory()

        _image = self._get_image(div[0].img['src'], tmp_folder.name)
        b64_image = self.process_image(_image, tmp_folder.name)
        guess_uuid = solver.solve(base64=b64_image)

        while True:
            guess = solver.result(guess_uuid)

            if guess is None:
                time.sleep(5)
            else:
                break

        error = captcha_page_soup.find(id="message_error")
        if error:
            message = error.get_text()
            # Enter the characters as they are given in the challenge.
            raise Exception(message)

        form = captcha_page_soup.find('form', class_='cvf-widget-form-captcha')

        data = {'metadata1': self.session()._metadata1_generator.generate()}

        for field in form.find_all('input'):
            name = field.get('name')
            if not name:
                continue
            value = field.get('value')
            data[name] = value
                
        data['cvf_captcha_input'] = guess
        verify = self.session()._post(
            "https://www.amazon.com/ap/cvf/verify",
            data=data
        )
        soup = BeautifulSoup(verify.text, 'html.parser')
        if soup.find_all(class_='cvf-widget-alert-id-cvf-captcha-error'):
            try:
                solver.incorrect(guess_uuid)
            except Exception as e:
                print (f"ERROR Reporting {e}")
            return self.request_otp_forgot_password(email)

        self.__reset_page = self.session()._get(
            verify.url
        )
        tmp_folder.cleanup()
        return self.__reset_page
    
    def _get_image(self, image_url, tmp_folder) -> Image:
        r = self.session()._get(image_url, stream = True)
        tmp_img = f'{tmp_folder}/original'

        # Check if the image was retrieved successfully
        if r.status_code == 200:
            # Set decode_content value to True, otherwise the downloaded image file's size will be zero.
            r.raw.decode_content = True
            
            # Open a local file with wb ( write binary ) permission.
            with open(tmp_img,'wb') as f:
                shutil.copyfileobj(r.raw, f)
        else:
            raise IOError('Could not download: %s', image_url)

        return Image.open(tmp_img)

    def process_image(self, imageObject:Image, tmp_folder:str):
        images = []
        buffered = BytesIO()
        if imageObject.format != 'GIF':
            imageObject.save(fp=buffered, format=imageObject.format.lower())
        else:
            for frame in range(0,imageObject.n_frames, 6):
                imageObject.seek(frame)
                imageObject.save(f'{tmp_folder}/image_{frame}.gif')
                images.append(Image.open(f'{tmp_folder}/image_{frame}.gif'))

            gif = images[0]
            gif.save(fp=buffered, format='gif', save_all=True, append_images=images[1:], duration=250)

        buffered.seek(0)
        img_byte = buffered.getvalue()
        img_str = f"data:image/{imageObject.format.lower()};base64," + base64.b64encode(img_byte).decode()

        return img_str

    def retrieve_otp_from_email(self, content):
        """
        Parses the AWS Email to retrieve the OTP.
        """
        soup = BeautifulSoup(content, 'html.parser')
        otp = soup.find(id="verificationMsg").find(class_='otp').contents[0]
        return otp

    def reset_password_coupled(self, password, otp, request=None):
        """
        Performs a password reset in the Coupled Account.
        """
        if not request and not self.__reset_page:
            raise ValueError('Missing request information')
        if not request:
            request = self.__reset_page

        soup = BeautifulSoup(request.text, 'html.parser')
        form = soup.find(id="verification-code-form")

        data = {'metadata1': self.session()._metadata1_generator.generate()}
        for field in form.find_all('input'):
            name = field.get('name')
            if not name:
                continue
            value = field.get('value')
            data[name] = value
        
        data['code'] = otp

        verify = self.session()._post(
            "https://www.amazon.com/ap/cvf/verify",
            data=data
        )

        reset_password = BeautifulSoup(verify.text, 'html.parser')

        form = reset_password.find('form', id="ap_fpp_1d_form")
        data = {}
        for field in form.find_all('input'):
            name = field.get('name')
            if not name:
                continue
            value = field.get('value')
            data[name] = value
        data['password'] = password
        data['passwordCheck'] = password

        submit_password = self.session()._post(
            form.get("action"),
            data=data
        )
        soup_submit_password = BeautifulSoup(submit_password.text, 'html.parser')

        if soup_submit_password.find_all('div', id="message_success"):
            return True
        else:
            return False

import uuid
import sys
import base64
import urllib.request

def url_to_base64(url):
    return base64.b64encode(urllib.request.urlopen(url).read()).decode()

def show_image(b64):
    sys.stdout.write("\033]1337;File=")
    sys.stdout.write("name=captcha;inline=1:")
    sys.stdout.write(b64)
    sys.stdout.write("\a\n")

class iTermSolver:
    def __init__(self):
        self.jobs = {}
    
    def solve(self, base64=None, url=None):
        job_id = uuid.uuid4()

        if base64:
            b64 = base64
        elif url:
            b64 = url_to_base64(url)
        else:
            raise Exception("pass `url` or `base64`")

        self.jobs[job_id] = None
        show_image(b64)
        self.jobs[job_id] = input("Guess: ")

        return job_id
        
    def result(self, job_id):
        job_id = uuid.UUID(str(job_id))
        if job_id in self.jobs:
            return self.jobs[job_id]
        else:
            return None

    def incorrect(self, job_id):
        print("You guessed wrong!")

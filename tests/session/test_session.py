from tests import mock, BaseTestCase
import coto

class TestSession(BaseTestCase):

    def test_plain(self):
        session = coto.Session()

        self.assertEqual(False, session.debug)

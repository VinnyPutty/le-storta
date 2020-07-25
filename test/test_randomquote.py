import unittest

from basic_bot import *


def verify_root_cwd():
    if os.path.basename(os.getcwd()) != 'le-storta':
        print('Run tests from root directory.', file=sys.stdout)
        return False
    return True

class TestContext:

    def __init__(self):
        self.res = None


class MyTestCase(unittest.TestCase):

    def test_something(self):
        if not verify_root_cwd():
            return
        print(os.getcwd())
        # os.chdir('le-storta/')
        print(os.getcwd())
        self.assertEqual(True, 1)

    def test_pass(self):
        if not verify_root_cwd():
            return
        self.assertTrue(True)

    def test_fail(self):
        if not verify_root_cwd():
            return
        self.assertFalse(True)


if __name__ == '__main__':
    unittest.main()

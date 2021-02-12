
import os

def setup():
    test_artifacts_dir = 'tests/artifacts'
    if os.path.isdir(test_artifacts_dir):
        for filename in os.listdir(test_artifacts_dir):
            pathname = os.path.join(test_artifacts_dir, filename)
            os.remove(pathname)

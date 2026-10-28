
import os
import shutil


def force_remove_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"Successfully removed {path}")
    else:
        print(f"{path} does not exist")

def setup():
    test_artifacts_dir = 'tests/artifacts'
    if os.path.isdir(test_artifacts_dir):
        for filename in os.listdir(test_artifacts_dir):
            pathname = os.path.join(test_artifacts_dir, filename)
            os.remove(pathname)

    force_remove_directory('ZoomFoundry.egg-info')

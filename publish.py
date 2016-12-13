import subprocess

subprocess.call('pip install wheel'.split())
subprocess.call('python setup.py clean --all'.split())
subprocess.call('python setup.py sdist'.split())
# subprocess.call('pip wheel --no-index --no-deps --wheel-dir dist dist/*.tar.gz'.split())
subprocess.call('python setup.py register sdist bdist_wheel upload'.split())

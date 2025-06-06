import sys

def test_python_version():
    major, minor = sys.version_info[:2]
    assert (major, minor) >= (3, 12), f"Python 3.12 ou superior é necessário. Versão atual: {major}.{minor}"

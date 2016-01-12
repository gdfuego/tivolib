from distutils.core import setup

setup(name='tivolib',
      version='0.9',
      description='Python module for downloading shows from a TiVo',
      author='Gregory Boyce',
      author_email='gregory.boyce@gmail.com',
      url='https://github.com/gdfuego/tivolib',
      py_modules = ['tivolib'],
      scripts=['tivo', 'tsearch']
      )


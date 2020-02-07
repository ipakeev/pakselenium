from setuptools import setup, find_packages

setup(
    name='pakselenium',
    version='0.2.6',
    packages=find_packages(),
    url='https://github.com/ipakeev',
    license='MIT',
    author='Ipakeev',
    author_email='ipakeev93@gmail.com',
    description='Selenium Wrapper',
    install_requires=['selenium', 'urllib3']
)

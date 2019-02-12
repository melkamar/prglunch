from setuptools import setup
import prglunch.__version__

setup(
    name='prglunch',
    version=prglunch.__version__.__version__,
    description="Automatic scraping and slack-posting of lunch menus around the Prague office",
    long_description='Automatic scraping and slack-posting of lunch menus around the Prague office',
    author='Martin Melka',
    author_email='martin.melka@rohea.com',
    license='MIT',
    install_requires=['requests', 'beautifulsoup4'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest']
)

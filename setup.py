import os
import re
from setuptools import find_packages, setup


def get_version():
    with open(os.path.join(os.path.dirname(__file__), 'pretix_betterpos', 'apps.py'), encoding='utf-8') as f:
        content = f.read()
        match = re.search(r"__version__\s*=\s*'([^']+)'", content)
        if match:
            return match.group(1)
        raise RuntimeError('Unable to determine version')


with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='pretix-betterpos',
    version=get_version(),
    description='On-site POS plugin for Pretix',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='BetterPOS Team',
    url='https://example.invalid/pretix-betterpos',
    license='Apache-2.0',
    install_requires=[],
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    entry_points='''
[pretix.plugin]
pretix_betterpos=pretix_betterpos:PluginApp.PretixPluginMeta
''',
)

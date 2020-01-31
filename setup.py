import os
import sys
from setuptools import setup, find_packages
from tethys_apps.app_installation import custom_develop_command, custom_install_command

# -- Apps Definition -- #
app_package = 'crazysearch'
release_package = 'tethysapp-' + app_package
app_class = 'crazysearch.app:Crazysearch'
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)

# -- Python Dependencies -- #
dependencies = []

setup(
    name=release_package,
    version='0.0.1',
    tags='&quot;Hydroserver&quot;, &quot;Query&quot;,&quot;BYU&quot;,&quot;Geoglows&quot;, &quot;Data Share&quot;',
    description='This app is query tool in which data from different hydroservers and catalogs can be added and query, so the user can see  different data available',
    long_description='',
    keywords='',
    author='Giovanni Romero',
    author_email='gio.busrom@gmail.com',
    url='',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    cmdclass={
        'install': custom_install_command(app_package, app_package_dir, dependencies),
        'develop': custom_develop_command(app_package, app_package_dir, dependencies)
    }
)

from setuptools import find_packages, setup

package_name = 'create3_il'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='luna',
    maintainer_email='luna@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'il_data_collector = create3_il.il_data_collector:main',
        'bc_inference_node = create3_il.bc_inference_node:main',
        'dagger_session_node = create3_il.dagger_session_node:main',
        ],

    },
)

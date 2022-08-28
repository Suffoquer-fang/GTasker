from setuptools import setup, find_packages
from gtasker import __version__
with open('requirements.txt') as f:
    requirements = f.readlines()
  
long_description = 'GTasker Demo Package'
  
setup(
        name ='gtasker',
        version =__version__,
        author ='Suffoquer',
        author_email ='1161290791@qq.com',
        # url ='https://github.com/Suffoquer-fang/gtasker',
        description ='Demo Package for GTasker.',
        long_description = long_description,
        long_description_content_type ="text/markdown",
        license ='MIT',
        packages = find_packages(),
        entry_points ={
            'console_scripts': [
                'gta = gtasker.cmdparser:main'
            ]
        },
        classifiers =[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
        ],
        keywords ='gpu tasker',
        install_requires = requirements,
        zip_safe = False
)
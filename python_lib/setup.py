# python setup.py sdist
# python -m twine upload dist/*
 
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='ucanlintools',  
     version='0.1.0',
     author="ucan",
     author_email="ucandevices@mail.com",
     description="Local Interconnect Network (LIN) support for python",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/uCAN-LIN/LinUSBConverter",
     packages = ['ucanlintools'],
     package_data = { '': ['*.lark'] },
     license = 'MIT',
     keywords = ['LIN', 'LDF', 'LUC', 'uCAN', 'parser', 'mcp', 'car-hacking'],
     install_requires = ['pyserial','lark', 'bitstruct'],
     extras_require = {'mcp': ['mcp>=2']},
     entry_points = {'console_scripts': ['ucanlin-mcp=ucanlintools.mcp_server:main']},

     py_modules=['LUC','LDF_parser', 'LINFrame'],
     classifiers=[
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
     project_urls={
        "Documentation": "https://ucandevices.github.io/",
        "Source Code": "https://github.com/uCAN-LIN/LinUSBConverter/tree/master/python_lib",
     }
 )
rm -fr dist build
pyinstaller --name picktrue-metmuseum --onefile --icon=files/icon.ico picktrue/sites/metmuseum.py

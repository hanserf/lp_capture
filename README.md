# lp_capture
Tool for digitizing musical recordings



## Development:
``` bash
virtualenv -p python3 venv
source venv/bin/activate
python3 setup.py install

cd app
python3 main.py -l
# Find your sound device in the list [n]
python3 main.py -d n 
# The gui should launch
```

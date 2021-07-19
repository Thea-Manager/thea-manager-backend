find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

python3 application.py
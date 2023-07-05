# setup
```bash
sudo apt-get update
sudo apt-get install python3-pip python3-dev nginx python3-venv -y
alias venv="if [ -e ./.venv/bin/activate ]; then source ./.venv/bin/activate; else python3.10 -m venv .venv && source ./.venv/bin/activate; fi"
venv
```

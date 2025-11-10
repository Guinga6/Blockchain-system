# Blockchain Example

Simple educational implementation of a blockchain with a small Flask REST API.

This project contains two runnable nodes:
- `blockchain.py` (default node, runs on port 5000)
- `blockchain_node2.py` (second node, runs on port 5001)

## Features
- Simple proof-of-work blockchain
- Endpoints to mine blocks, create transactions, view the chain
- Node registration and a simple consensus algorithm (replace chain with longest valid chain)

## Requirements
- Python 3.8+ (or a recent Python 3.x)
- pip
- The Python packages: Flask, requests

## Quick setup (Windows PowerShell)

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install flask requests
```

3. (Optional) Save dependencies:

```powershell
python -m pip freeze > requirements.txt
```

## Run the nodes

Open two PowerShell windows (or use separate terminals):

Terminal 1 (node 1):

```powershell
# from project root
python blockchain.py
```

Terminal 2 (node 2):

```powershell
# from project root
python blockchain_node2.py
```

Node 1 will listen on port 5000, node 2 on port 5001.

## Example usage (API)

Mine a block (GET):

```powershell
Invoke-RestMethod -Uri http://localhost:5000/mine -Method GET
# or using curl
curl http://localhost:5000/mine
```

Create a transaction (POST):

```powershell
Invoke-RestMethod -Uri http://localhost:5000/transactions/new -Method POST -Body (@{sender='A'; recipient='B'; amount=5} | ConvertTo-Json) -ContentType 'application/json'
```

Get the full chain:

```powershell
curl http://localhost:5000/get_chain
```

Register nodes (to add peers):

```powershell
Invoke-RestMethod -Uri http://localhost:5000/nodes/register -Method POST -Body (@{nodes=@('http://127.0.0.1:5001')} | ConvertTo-Json) -ContentType 'application/json'
```

Resolve consensus (ask nodes to reconcile to the longest valid chain):

```powershell
curl http://localhost:5000/nodes/resolve
```

## Notes
- The code is educational and not production-ready.
- Difficulty is fixed via the `MINING_DIFFICULTY` constant (4 leading zeros).
- If you need a different port, open the file and change the `app.run(..., port=...)` value.

## Help / Next steps
- I can add a `requirements.txt` if you'd like.
- I can also add a short script to run both nodes with different ports automatically.

---

If you'd like this README modified (language, more details, or a CONTRIBUTING section), tell me what to add.

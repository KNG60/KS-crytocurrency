## Uruchomienie węzłów

```bash
python ../run_node.py

python ../run_node.py --port 5001 --seeds 127.0.0.1:5000

python ../run_node.py --port 5002 --seeds 127.0.0.1:5001
```

### Pomoc

```bash
python ../run_node.py --help
```

### Lista peerów

```bash
curl http://127.0.0.1:5000/peers
```

### Ping węzła

```bash
curl http://127.0.0.1:5000/ping
```

### Dodanie peera

```bash
curl -X POST http://127.0.0.1:5000/peers \
  -H "Content-Type: application/json" \
  -d '{"host": "127.0.0.1", "port": 5001}'
```
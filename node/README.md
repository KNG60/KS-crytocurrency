## Wyczyszczenie baz danych

```bash
rm -r db/*
```

## Uruchomienie węzłów

```bash
# Węzeł startowy (bootstrap)
python ../run_node.py

# Węzeł dołączający się (z seedem)
python ../run_node.py --port 5001 --role normal --seeds 127.0.0.1:5000

# Kolejny węzeł (koparka)
python ../run_node.py --port 5002 --role miner --seeds 127.0.0.1:5000
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

### Odczyt łańcucha bloków

```bash
curl http://127.0.0.1:5000/blocks
```

### Zlecenie wykopania bloku

```bash
curl -X POST http://127.0.0.1:5002/mine
```
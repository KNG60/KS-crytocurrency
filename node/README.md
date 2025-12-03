## Wyczyszczenie baz danych

```bash
rm -r db/*
```

## Uruchomienie węzłów

**Każdy węzeł wymaga klucza publicznego z portfela.**

Utwórz konto w portfelu:

```bash
python ../run_wallet.py add alice
```

Uruchom węzeł używając label z portfela:

```bash
# Węzeł startowy (bootstrap)
python ../run_node.py --wallet-label alice

# Węzeł dołączający się (z seedem)
python ../run_node.py --port 5001 --role normal --wallet-label bob --seeds 127.0.0.1:5000

# Węzeł górniczy
python ../run_node.py --port 5002 --role miner --wallet-label charlie --seeds 127.0.0.1:5000
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
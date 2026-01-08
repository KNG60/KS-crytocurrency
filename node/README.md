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

### Informacje o węźle (łańcuch + forki + mempool)

```bash
curl http://127.0.0.1:5000/info
```

### Zlecenie wykopania bloku

```bash
curl -X POST http://127.0.0.1:5002/mine
```

### Sterowanie górnikiem (API)

Uruchomienie / zatrzymanie pracy minera oraz podgląd statusu:

```bash
# Start minera na porcie 5002
curl -X POST http://127.0.0.1:5002/miner/start

# Stop minera
curl -X POST http://127.0.0.1:5002/miner/stop

# Status pracy minera
curl http://127.0.0.1:5002/miner/status
```

W wizualizacji sieci węzeł górniczy jest złoty, gdy kopie (running), oraz szary, gdy jest zatrzymany (stopped).

## Graph Manager (wizualizacja sieci)

Strona wizualizacji: http://127.0.0.1:8080/static/network.html

### Uruchomienie menedżera

```bash
python -c "from demo.graph_manager import CentralizedGraphManager; import logging; logging.basicConfig(level=20); CentralizedGraphManager('127.0.0.1', 8080).run()"
```

W UI dostępne są: popup z informacjami o węźle (Blockchain, Fork Chain, Pending Transactions), przyciski Start/Stop minera oraz automatyczne kolorowanie węzłów górniczych w zależności od statusu.

### Symulacja ataku (fork attack demo)

Skrypt demonstracyjny wymuszający powstawanie forków przez wstrzyknięcie krótkiej „sierociej” gałęzi bloków (na przestarzałym rodzicu) do wybranych węzłów-ofiar:

```bash
python demo/run_fork_attack.py
```

Opis działania:
- uruchamia menedżera grafu oraz losową sieć węzłów (część jako miners),
- wybiera starszego rodzica względem tip i lokalnie „kopie” krótką gałąź orphanów,
- rozsyła te bloki do wybranych węzłów-ofiar, co skutkuje zbuforowaniem ich jako forki (widoczne w UI).



### 1) Utwórz konto dla nowego węzła

```bash
python ../run_wallet.py add node_5010
```

### 2) Start węzła bez seedów (samodzielnie, z własnym genesis)

```bash
python ../run_node.py --host 127.0.0.1 --port 5010 --role normal --wallet-label node_5010 --centralized-manager http://127.0.0.1:8080
```


### 3) Start węzła z seedem (automatyczne dołączenie do sieci)

```bash
python ../run_node.py --host 127.0.0.1 --port 5010 --role normal --wallet-label node_5010 --seeds 127.0.0.1:5000 --centralized-manager http://127.0.0.1:8080
```

### 4) Dodanie peera do istniejącego węzła

Dodajemy adres innego węzła do listy peerów danego noda (operacja jednostronna – warto dodać wpis w obie strony):

```bash
# Dodaj 127.0.0.1:5010 jako peera węzła 5000
curl -X POST http://127.0.0.1:5000/peers \
	-H "Content-Type: application/json" \
	-d "{\"host\":\"127.0.0.1\",\"port\":5010}"

# (opcjonalnie) Dodaj 127.0.0.1:5000 jako peera węzła 5010 – połączenie dwukierunkowe
curl -X POST http://127.0.0.1:5010/peers \
	-H "Content-Type: application/json" \
	-d "{\"host\":\"127.0.0.1\",\"port\":5000}"

# Weryfikacja
curl http://127.0.0.1:5000/peers
curl http://127.0.0.1:5010/peers
```
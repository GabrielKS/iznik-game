# iznik-game
This is a repository for the Iznik game, created by Gabriel Konar-Steenberg in summer 2020.

## Usage
To run the server:
```
python3 server.py
```
URLs look like: [http://localhost:5000/basic-cli/play](http://localhost:5000/basic-cli/play)

To update the client:
Old way:
```
tsc --watch
```
New way, which also transforms imports:
```
node "node_modules/tsc-watch/lib/tsc-watch.js" --onCompilationComplete "python3 transform_import.py"
```

To manage packages:
```
npm install
```

To run the mockup game or other things nested in packages:
```
python3 -m simulation.main
```
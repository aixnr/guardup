build:
	pyinstaller --onefile guardup.py

run:
	sudo ./dist/guardup init && sudo ./dist/guardup host

testuser:
	sudo ./dist/guardup mngr --mode add --peer Nebula --address 10.0.0.11 --allowed 10.0.0.0

clean:
	rm -rf build dist *.spec

uninstall:
	sudo rm -rf /var/guardup

dir:
	sudo mkdir -p /var/guardup

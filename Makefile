build:
	pyinstaller --onefile guardup.py

clean:
	rm -rf build dist *.spec

uninstall:
	sudo rm -rf /var/guardup
	sudo rm /usr/local/bin/guardup

install: build
	sudo cp ./dist/guardup /usr/local/bin/guardup

dir:
	sudo mkdir -p /var/guardup

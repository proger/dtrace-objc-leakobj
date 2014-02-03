PID ?= $(shell pgrep -f clojure.main)

nsnotifications nsobject:
	rm -rf leaks
	python leakexpand.py leakspecs/$@.yaml
	make -C leaks/$@
	make -C leaks/$@ apply PID=$(PID)

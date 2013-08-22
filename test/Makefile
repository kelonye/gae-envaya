start: lib
	@dev_appserver.py . --port 8005 --admin_port 5000

test: lib
	@python tests.py -f

lib:
	@ln -fs $(PWD)/$@ $@

.PHONY: test start

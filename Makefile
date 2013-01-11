ALL_TARGETS = pydosh/Ui_pydosh.py pydosh/pydosh_rc.py 

all: $(ALL_TARGETS) 

pydosh/pydosh_rc.py: ui/pydosh.qrc
	pyrcc4 $? -o $@

pydosh/Ui_pydosh.py: ui/pydosh.ui
	pyuic4 $? -o $@

clean:
	@rm -f $(ALL_TARGETS)

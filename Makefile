ALL_TARGETS = pydosh/ui_pydosh.py pydosh/pydosh_rc.py pydosh/ui_settings.py pydosh/ui_login.py pydosh/ui_help.py pydosh/ui_tags.py

all: $(ALL_TARGETS) 

pydosh/pydosh_rc.py: ui/pydosh.qrc
	pyrcc4 $? -o $@

pydosh/ui_pydosh.py: ui/pydosh.ui
	pyuic4 $? -o $@

pydosh/ui_login.py: ui/login.ui
	pyuic4 $? -o $@

pydosh/ui_settings.py: ui/settings.ui
	pyuic4 $? -o $@

pydosh/ui_help.py: ui/help.ui
	pyuic4 $? -o $@

pydosh/ui_tags.py: ui/tags.ui
	pyuic4 $? -o $@

clean:
	@rm -f $(ALL_TARGETS) pydosh/*.pyc

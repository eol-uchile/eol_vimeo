.DEFAULT_GOAL := help
.PHONY: requirements

# include *.mk

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please use \`make <target>' where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m %-25s\033[0m %s\n", $$1, $$2}'

lang_targets = en es_419
_extract_translations:
	pybabel extract -F eol_vimeo/locale/babel.cfg -o eol_vimeo/locale/django.pot --msgid-bugs-address=eol-ing@uchile.cl --copyright-holder='Oficina EOL' --project=xblock-in-video-quiz --version=1.0.0 --last-translator='Oficina EOL <eol-ing@uchile.cl>' *
	pybabel extract -F eol_vimeo/locale/babel-js.cfg -o eol_vimeo/locale/django-js.pot --msgid-bugs-address=eol-ing@uchile.cl --copyright-holder='Oficina EOL' --project=xblock-in-video-quiz --version=1.0.0 --last-translator='Oficina EOL <eol-ing@uchile.cl>' *

create_translations_catalogs: _extract_translations ## Create the initial configuration of .po files for translation
	for lang in $(lang_targets) ; do \
		pybabel init -i eol_vimeo/locale/django.pot -D django -d eol_vimeo/locale/ -l $$lang ; \
		pybabel init -i eol_vimeo/locale/django-js.pot -D djangojs -d eol_vimeo/locale/ -l $$lang ; \
	done

update_translations: _extract_translations ## update strings to be translated
	pybabel update -N -D django -i eol_vimeo/locale/django.pot -d eol_vimeo/locale/
	pybabel update -N -D djangojs -i eol_vimeo/locale/django-js.pot -d eol_vimeo/locale/
	rm eol_vimeo/locale/django.pot
	rm eol_vimeo/locale/django-js.pot

compile_translations: ## compile .po files into .mo files
	pybabel compile -f -D django -d eol_vimeo/locale/; \
	pybabel compile -f -D djangojs -d eol_vimeo/locale/

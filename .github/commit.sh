#!/usr/bin/bash

prepare_commit() {
  git config --global user.name "eolito"
  git config --global user.email 'eol-uchile@users.noreply.github.com'
  git add coverage-badge.svg
  git commit -m "Update coverage badge" 2> /dev/null
  if [ $? -eq 0 ]; then
    git push https://eolito:${{ secrets.GITHUB_TOKEN }}@github.com/eol-uchile/eol_vimeo.git HEAD:master;
  else
    echo "Skipped";
  fi
  # Force 0 as output
  echo "Completed"
}

prepare_commit $1

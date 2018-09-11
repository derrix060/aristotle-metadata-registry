#!/bin/bash

TOX_ENV_TO_RUN=$1

if [ "$TRAVIS_BRANCH" = "master" ] || ./scripts/check_path.sh $MODULE_PATH || ./scripts/check_path.sh python/aristotle-metadata-registry; then
  tox -e $TOX_ENV_TO_RUN --skip-missing-interpreters
  export OUT_CODE=$?
fi;

exit $OUT_CODE

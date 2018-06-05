export MODULE=$1
cd $TRAVIS_BUILD_DIR/python/$MODULE
coveralls
export OUT_CODE=$?
cd -

exit $OUT_CODE
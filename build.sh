#!/usr/bin/env bash
# exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/.render

# Install Chrome
if [[ ! -d $STORAGE_DIR/chrome ]]; then
  echo "...Downloading Chrome"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

  # Extract the .deb package without dpkg
  ar x google-chrome-stable_current_amd64.deb
  tar -xvf data.tar.xz -C $STORAGE_DIR/chrome

  # Clean up
  rm google-chrome-stable_current_amd64.deb control.tar.gz data.tar.xz debian-binary

  cd $HOME/project/src # Make sure we return to where we were
else
  echo "...Using Chrome from cache"
fi

# Install ChromeDriver
if [[ ! -d $STORAGE_DIR/chromedriver ]]; then
  echo "...Downloading ChromeDriver"
  mkdir -p $STORAGE_DIR/chromedriver
  cd $STORAGE_DIR/chromedriver

  # Updated URL to download the latest ChromeDriver version
  wget https://storage.googleapis.com/chrome-for-testing-public/127.0.6533.99/linux64/chromedriver-linux64.zip

  unzip chromedriver-linux64.zip
  mv chromedriver-linux64/chromedriver $STORAGE_DIR/chromedriver/chromedriver
  rm -r chromedriver-linux64 chromedriver-linux64.zip
  cd $HOME/project/src # Make sure we return to where we were
else
  echo "...Using ChromeDriver from cache"
fi

# Be sure to add Chrome and ChromeDriver location to the PATH as part of your Start Command
# export PATH="${PATH}:/opt/render/project/.render/chrome/opt/google/chrome"
# export PATH="${PATH}:/opt/render/project/.render/chromedriver"

# Add your own build commands...

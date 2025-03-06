
echo "**************************************************"
echo "**************************************************"
echo "**************************************************"
echo "**************************************************"

# install google chrome 133.0.6943.141
wget -P /tmp http://dl.google.com/linux/chrome/deb/pool/main/g/google-chrome-stable/google-chrome-stable_133.0.6943.141-1_amd64.deb
dpkg --force-all -i /tmp/google-chrome-stable_133.0.6943.141-1_amd64.deb || true
apt-get update -qqq
apt-get install -f -y -qqq

google-chrome --version

echo "**************************************************"
echo "**************************************************"
echo "**************************************************"
echo "**************************************************"

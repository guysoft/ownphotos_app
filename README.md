# ownphotos_app

An app to run ownphotos, currently as proof of concept.

## Build insrtuctions

```
mkdir kivy
cd kivy
git clone https://github.com/kivy/python-for-android.git
git clone https://github.com/guysoft/ownphotos_app.git
cd ownphotos_app
sudo docker-compose up -d
sudo docker exec -it -u 0 buildozer-ownphotos pip3 install https://github.com/kivy/buildozer/archive/master.zip
./docker_build
```

Debug with:
```
./docker_debug
```

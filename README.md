# Base FastAPI Web Project
## Установка docker под Ubuntu/Debian Linux:
```sh
# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
```

## Первоначальная настройка docker:
```sh
sudo usermod -aG docker $USER
```
После этого выйдите из учётной записи пользователя и залогиньтесь назад, или перезапустите компьютер.


## Как запустить проект:
```sh
docker compose up --build
```

# Для Windows
![Miku gif](https://media1.tenor.com/m/FZZqna91PwQAAAAC/miku-hatsune-miku.gif)
Скачиваем в интернете Докер, а дальше сами 0w0 


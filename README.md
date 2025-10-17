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

## Установка docker на Arch:
```sh
sudo pacman -Sy docker
sudo pacman -Sy docker-compose
```
Или
```sh
yay -S docker
yay -S docker-compose
```

## Для Windows
![Miku gif](https://media1.tenor.com/m/FZZqna91PwQAAAAC/miku-hatsune-miku.gif)

[Скачать Docker Desktop](https://www.docker.com/) | [Скачать Git](https://git-scm.com/)<br>
***Установка только с божьей помощью.***

## Первоначальная настройка Docker в Linux:
```sh
sudo usermod -aG docker $USER
```
После этого выйдите из учётной записи пользователя и залогиньтесь назад, или перезапустите компьютер.

## Как запустить проект:
```sh
docker compose up --build
```

## Как пересобрать проект полностью
```sh
docker compose build --no-cache web
```

## Как войти в окружение базы данных MySQL для ручного управления
```sh
docker-compose exec db mysql -u fastapi_user -pfastapi_pass fastapi_db
```

## Ошибки базы данных при мажорном обновлении
Удалите папку **``mysql_data``** и запустите проект заново.

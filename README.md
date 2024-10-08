# 又一個學校內容管理系統

## 預設帳號

<http://demo.bjes.tp.edu.tw>

最高管理者帳號密碼為 admin / admin4yascms

一般使用者有兩組帳號，一組是 user1 / user1 ，另一組是 user2 / user2 。

## 如何回報問題

若您對網站的功能有各種功能上的建議，或是發現 bugs，都歡迎回報讓我們知道！ 回報的網址在 <https://github.com/fossnio/yascms/issues> ，您需要先申請 [GitHub](https://github.com) 的帳號才能上去建立 issue 回報。

## 如何開發

若對參與開發有興趣，歡迎來信：

- William Wu <william _AT_ pylabs.org>

### 將原始碼 clone 至本機

```shell
export GIT_BASE_DIR=~/git
mkdir -p $GIT_BASE_DIR
cd $GIT_BASE_DIR
git clone https://github.com/fossnio/yascms.git
```

### 建立開發環境

可以選擇使用 ansible playbook 建置，或是手動建置，以下說明此兩種作法，請擇一使用。

#### 使用 ansible playbook 建置

* 使用 pip3 安裝 ansible

```shell
mkdir -p ~/venv
python3 -m venv ~/venv/pipx
~/venv/pipx/bin/pip install pipx
~/venv/pipx/bin/pipx install ansible
```

* 使用 ansible playbook 建置開發環境，注意執行此指令的帳號需有 sudo root 的權限

```shell
~/.local/bin/ansible-playbook develop.yml
```

#### 手動建置

* 建立專案運行的 venv 環境

```shell
cd yascms
# 在 Debian 上需要安裝 python3-venv 套件
python3 -m venv .venv
```

* 更新套件管理工具

```shell
.venv/bin/pip install --upgrade pip setuptools poetry
```

* 同步開發專案需要安裝的套件

```shell
.venv/bin/poetry install
```


* 建立開發用的測試資料庫，並將資料庫 migrate 到最新版

```shell
cp development.ini.sample development.ini
# 至少要修改 development.ini 的 sqlalchemy.url 設定，
# 以對應實際的資料庫設定。請參考檔案內相關註解。
# 修改完成後再執行以下指令
.venv/bin/poetry run inv file.delete db.import-test-data
```


* 執行測試

```shell
.venv/bin/poetry run inv test.all
```

* 於本機開發環境啟動專案

```shell
.venv/bin/poetry run pserve development.ini --reload
```

## 使用套件

### 前端

- Bootstrap https://getbootstrap.com MIT License
- Bootstrap Icons https://icons.getbootstrap.com MIT License
- jQuery https://jquery.com MIT License
- jQuery Bonsai https://github.com/aexmachina/jquery-bonsai MIT License
- jQuery DateTimePicker https://github.com/xdan/datetimepicker MIT License
- jquery-qubit https://github.com/simonexmachina/jquery-qubit MIT License
- SmartMenus jQuery Website Menu Plugin https://www.smartmenus.org MIT License
- Summernote https://summernote.org/ MIT License
- Sortable https://github.com/SortableJS/Sortable MIT License

### 後端

請參閱 pyproject.toml

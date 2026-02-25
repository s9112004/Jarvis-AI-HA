# Ubuntu 24.04 Docker 安裝指南

請在您的 Ubuntu 虛擬機終端機 (Terminal) 中依序複製以下指令碼區塊並貼上執行。

清理舊版本（如果有的話，全新安裝可忽略但執行也無害）：
```bash
sudo apt-get update
sudo apt-get remove docker docker-engine docker.io containerd runc
```

安裝必要的系統工具：
```bash
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
```

將 Docker 官方儲存庫加入系統來源列表：
```bash
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

更新套件清單並正式安裝 Docker 與 Docker Compose 相關套件：
```bash
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

將目前使用者加入 docker 群組（這樣以後執行 docker 指令就不需要一直打 sudo）：
```bash
sudo usermod -aG docker $USER
newgrp docker
```

最後，測試 Docker 是否成功啟動並運行：
```bash
docker run hello-world
```

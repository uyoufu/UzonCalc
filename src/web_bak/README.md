# UZon Mail (uzoncalc)

A app for sending emails

## Install the dependencies
```bash
bun install
```

### Start the app in development mode (hot-code reloading, error reporting, etc.)
```bash
bun run dev
```


### Lint the files
```bash
bun run lint
```



### Build the app for production
```bash
bun run build
```

### Customize the configuration
See [Configuring quasar.config.js](https://v2.quasar.dev/quasar-cli-vite/quasar-config-js).


## Docker 容器远程开发

``` bash
cd ui-src
docker compose up -d
# 第一次需要安装依赖
docker exec -it uzoncalc-dev bun install && bun run dev
# 第二次启动
docker exec -it uzoncalc-dev bun run dev
```


## quasar 升级

### bun

参考 https://quasar.dev/start/upgrade-guide#with-quasar-cli
``` bash
# 安装 cli
bunx @quasar/cli

# 检查包
bunx @quasar/cli upgrade

# 开始升级
bunx @quasar/cli upgrade --install
```

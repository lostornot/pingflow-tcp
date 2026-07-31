# PingFlow TCP

PingFlow TCP measures request-response latency inside a persistent TCP
connection and compares it with TCP connection latency.

它不是 ICMP Ping，也不是带宽测速工具。PingFlow 会先建立一条 TCP 连接，
然后在同一连接中持续发送小型请求，由服务端立即回显，用来发现“TCP
握手延迟正常，但真实数据交互明显更慢”以及少量长尾卡顿等问题。

## 功能

- 分别报告 TCP 建连 RTT 与已建立连接内的 request-response RTT
- 同时支持 IPv4 与 IPv6
- 一个服务端进程可同时监听 `0.0.0.0` 和 `[::]`
- 默认使用 1300 B 应用负载，也支持 32 B 或自定义负载大小
- 默认连续测试 20 秒，每秒显示一次实际区间结果
- 报告 min、median、p95、p99、max、长尾率和失败率
- 默认启用 `TCP_NODELAY`
- 支持 JSON 输出
- 单文件实现，仅依赖 Python 3 标准库

## 一行下载并运行

无需预先安装，也无需 `sudo`。下面的短入口通过 jsDelivr 下载固定版本并
校验 SHA-256，用户侧下载过程不需要连接 GitHub。

在 VPS 上一行下载并启动服务端：

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/lostornot/pingflow-tcp@main/i | sh -s -- -s
```

在本地一行下载、校验并运行客户端（将 `VPS_IP` 替换为 VPS 的 IPv4、
IPv6 或域名）：

```bash
curl -fsSL https://cdn.jsdelivr.net/gh/lostornot/pingflow-tcp@main/i | sh -s -- -c VPS_IP
```

两条命令都会使用临时目录，运行结束后自动清理，不会把 `pingflow` 安装
到系统中。VPS 服务端在前台运行，按 `Ctrl+C` 停止。

## 一键安装

Linux 和 macOS：

```bash
curl -fsSL https://github.com/lostornot/pingflow-tcp/releases/latest/download/install.sh | sudo sh
```

安装脚本会校验 Release 中 `pingflow` 文件的 SHA-256。若希望先检查安装
脚本，可以先下载再执行：

```bash
curl -fsSL https://github.com/lostornot/pingflow-tcp/releases/latest/download/install.sh -o install-pingflow.sh
less install-pingflow.sh
sudo sh install-pingflow.sh
```

要求：Python 3.8 或更高版本，以及 `curl` 或 `wget`。

## 使用

### VPS 服务端

默认同时监听 IPv4 和 IPv6 的 TCP 39001 端口：

```bash
pingflow -s
```

只监听 IPv4 或 IPv6：

```bash
pingflow -s -4
pingflow -s -6
```

如果服务器启用了防火墙，需要临时允许测试端口，例如：

```bash
sudo ufw allow 39001/tcp
```

服务端默认在前台运行，按 `Ctrl+C` 停止。关闭启动它的 SSH 会话时，
服务端也会响应 `SIGHUP` 停止并释放监听端口。如果使用上面的“一行下载
并运行”命令，停止后临时文件也会自动删除。

如果提示 `TCP port 39001 is already in use`，说明已有 PingFlow 或其他
程序占用了该端口，可先在 VPS 上确认占用进程：

```bash
sudo ss -ltnp 'sport = :39001'
```

### 客户端

直接传入 IPv4 或 IPv6 地址时，PingFlow 会自动识别地址族，不需要
`-4` 或 `-6`：

```bash
pingflow -c 203.0.113.10
pingflow -c 2001:db8::10
```

不指定 `-S/--size` 或 `--sizes` 时，默认使用 **1300 B** 应用负载。
指定单一负载大小：

```bash
pingflow -c 203.0.113.10 -S 32
pingflow -c 203.0.113.10 --size 1300
```

这里的负载大小是每次测量时客户端发送、服务端原样回显的应用数据字节数。
例如 `-S 1300` 表示发送 1300 B 并接收 1300 B 回显。它不是 TCP 段或
IP 包的固定大小；TCP 仍可根据路径和系统状态拆分、合并或重传这些数据。
原有的 `-l/--length` 继续作为兼容别名。

IPv6 命令行地址不需要方括号。

一次测试 32 B 和 1300 B：

```bash
pingflow -c 203.0.113.10 --sizes 32,1300
```

`--sizes` 只在需要一次比较多个负载大小时使用。

默认先进行 10 次 TCP 建连探测，然后在一条已建立的 TCP 连接中连续测试
20 秒。每次都必须完整收到服务端回显后才发送下一次请求，不并发发送，
请求之间默认不额外等待。测试过程中每秒显示该秒内实际完成的样本数、
平均 RTT 和最大 RTT：

```text
[Request/Response RTT]   0.00-  1.00 sec    18/18   samples  avg 48.20 ms  max 55.31 ms
[Request/Response RTT]   1.00-  2.00 sec    19/19   samples  avg 47.85 ms  max 52.62 ms
```

p95 和 p99 只在测试结束时计算。最终默认只显示两行摘要：

```text
[TCP Connect] 10/10  median/p95=47.20/50.10 ms  errors=0
[Request/Response RTT] 372/375  median/p95/p99/max=48.10/53.20/61.40/68.30 ms  timeouts=3  errors=0
```

修改测试时间：

```bash
pingflow -c 203.0.113.10 -t 10
```

需要固定样本数时使用 `-n/--count`，它与 `-t/--time` 互斥：

```bash
pingflow -c 203.0.113.10 -n 100
```

`-v` 会显示每一条原始 request-response RTT。若需要主动降低采样频率，
可用 `-i/--interval` 在每次完成后增加等待时间；默认值为 `0`。

传入域名时，默认使用系统解析器返回的首选地址。只有需要强制地址族或
同时比较两种地址族时才使用 `-4`、`-6` 或 `--both`：

```bash
pingflow -c example.com -4
pingflow -c example.com -6
pingflow -c example.com --both --sizes 32,1300
```

复现较长测试：

```bash
pingflow -c 203.0.113.10 \
  --time 60 \
  --connect-count 20 \
  --timeout 1.5 \
  --sizes 32,1300
```

JSON 输出：

```bash
pingflow -c 203.0.113.10 -n 100 -J
```

查看全部参数：

```bash
pingflow --help
```

## 如何解读

正常情况：

```text
[TCP Connect] median:           50 ms
[Request/Response RTT] median:  51 ms
```

握手与连接内交互延迟基本一致。

疑似握手包与普通数据包处理不同：

```text
[TCP Connect] median:           50 ms
[Request/Response RTT] median: 170 ms
```

如果中位数正常，但 p99 或 max 偶尔跳到数百毫秒，则代表存在真实长尾。
这可能来自丢包重传、链路排队、Wi-Fi、本机调度或代理处理。

PingFlow 不能仅凭应用层结果直接给出原始丢包率，因为 TCP 会自动重传。
要确认长尾是否由丢包造成，仍需结合客户端与服务端抓包。后续版本计划在
支持的平台读取 `TCP_INFO`，补充 TCP 重传计数。

## 协议说明

客户端建立 TCP 连接后：

1. 协商协议版本与固定 payload 长度；
2. 完成若干次不计入结果的预热交互；
3. 每次只发送一个请求；
4. 等待服务端完整回显后再发送下一次请求；
5. 默认不增加额外等待，连续串行采样 20 秒；
6. 使用单调高精度时钟测量每次完整 request-response RTT。

服务端只接受 PingFlow 协议，payload 上限为 1 MiB，且响应大小与请求
大小相同，不提供 UDP 服务。

## 安全提示

PingFlow 服务端没有身份认证或加密。建议仅在测试期间开放端口，完成后
停止服务并删除临时防火墙规则：

```bash
sudo ufw delete allow 39001/tcp
```

## 与 iPerf3 的区别

iPerf3 主要测量最大可达带宽、吞吐和相关网络性能；PingFlow 专注于
一条已建立 TCP 连接中的小型 request-response 延迟。两者互补，
PingFlow 与 ESnet iPerf 项目无关。

## 开发

运行测试：

```bash
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)

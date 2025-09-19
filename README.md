# 批量发送邮件脚本使用说明

这个仓库提供了一个名为 `send_emails.py` 的 Python 脚本, 能够根据一份邮件模板和一份邮箱地址清单, 自动逐个发送邮件。脚本专为没有编程基础的用户设计, 只要准备好模板和收件人列表, 按照说明执行即可。

## 1. 环境准备

1. 在电脑上安装 [Python 3.8 及以上版本](https://www.python.org/downloads/)。
2. 下载或复制本仓库的 `send_emails.py` 文件到本地目录。
3. 打开终端(Windows 可使用“命令提示符”或 PowerShell, macOS/Linux 使用 Terminal)。

## 2. 准备邮件模板

新建一个普通的文本文件, 例如 `template.txt`, 内容格式如下:

```
Subject: 您好 {name}

这是一封示例邮件。
{name} 您好, 这是自动发送的内容。
```

* 第一行必须以 `Subject:` 开头, 后面是邮件主题。
* 正文可以写多行文字。
* 可以使用 `{name}` 这种占位符来插入收件人信息(下文会介绍如何提供)。

## 3. 准备收件人清单

使用 Excel 或者其他表格软件创建一个 CSV 文件, 例如 `recipients.csv`, 第一行是表头, 至少需要 `email` 这一列:

```
email,name
alice@example.com,小红
bob@example.com,小明
```

* `email` 列是必须的, 其他列(例如 `name`)可选。
* 如果模板中使用了 `{name}` 占位符, 则在 CSV 中需要存在 `name` 这一列。
* 保存文件时请选择“CSV UTF-8 (逗号分隔)”格式。

## 4. 运行脚本

在终端中切换到 `send_emails.py` 所在目录, 执行以下命令(请把示例参数替换成自己的信息):

```
python send_emails.py template.txt recipients.csv \
    --sender your_email@example.com \
    --smtp-host smtp.example.com \
    --smtp-port 587 \
    --smtp-user your_email@example.com
```

运行后程序会提示输入邮箱的登录密码或授权码(输入时不会显示)。

常用参数说明:

* `template.txt` / `recipients.csv` : 模板和收件人文件的路径。
* `--sender` : 发件人邮箱地址, 会出现在邮件的 From 字段。
* `--smtp-host` : 邮箱服务商提供的 SMTP 服务器地址(例如 QQ 邮箱是 `smtp.qq.com`)。
* `--smtp-port` : SMTP 端口, 常见的有 587(默认, 需要 STARTTLS) 或 465(SSL)。
* `--smtp-user` : 登录 SMTP 服务器的用户名, 通常就是邮箱地址。
* `--use-ssl` : 如果你的邮箱服务商要求使用 SSL(常见于端口 465), 就在命令末尾加上该选项。
* `--no-starttls` : 某些旧服务器不支持 STARTTLS, 可以加上这个选项关闭加密启动。
* `--password` : 直接在命令中提供密码或授权码(不推荐, 为了安全请尽量手动输入)。
* `--dry-run` : 只预览最终邮件内容, 不实际发送, 用于检查格式。

## 5. 先做预览

建议先执行一次预览, 确认主题和正文是否正确:

```
python send_emails.py template.txt recipients.csv \
    --sender your_email@example.com \
    --smtp-host smtp.example.com \
    --smtp-port 587 \
    --smtp-user your_email@example.com \
    --dry-run
```

程序会在终端中显示每一封邮件的主题和正文, 但不会真正发送。

## 6. 正式发送

确认无误后, 去掉 `--dry-run` 重新运行命令, 按提示输入密码或授权码即可发送。发送过程中, 终端会显示每一个邮箱的发送状态。

## 7. 常见问题

* **SMTP 密码或授权码是什么?** 很多邮箱服务商不会使用你的登录密码, 而是需要到邮箱设置里生成一个“授权码”用于第三方客户端登录。
* **如何获取 SMTP 服务器地址?** 可以在邮箱服务商的帮助中心搜索“SMTP 设置”, 常见邮箱如 QQ、163、Gmail 都会提供详细说明。
* **发送失败怎么办?**
  * 检查邮箱是否开启了 SMTP/IMAP 服务。
  * 确认授权码是否正确。
  * 有些服务商限制短时间内的发送数量, 需要等待一段时间或申请企业邮件服务。
  * 如果报错提示缺少某个占位符, 请确认 CSV 文件里是否存在对应的列。

按照以上步骤, 即便没有编程基础, 也可以顺利批量发送邮件。祝使用顺利!

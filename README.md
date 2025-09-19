# 自动群发邮件脚本

这个仓库提供了一个基于 Python 的小工具, 能够读取一份邮件模板和一份收件人清单(CSV 格式),
并逐个向清单中的邮箱发送个性化邮件。脚本仅使用 Python 标准库, 不需要额外安装第三方库。

## 1. 准备环境

1. 安装 [Python 3.8+](https://www.python.org/downloads/)。
2. 确保你拥有一个支持 SMTP 的邮箱账号(例如 QQ 邮箱、163 邮箱、Gmail 等)。
3. 大多数邮箱为了安全会要求使用**授权码/应用专用密码**发送邮件, 请在邮箱设置中开启 SMTP 服务并
   获取该密码, 发送时不要使用真实登录密码。

## 2. 准备邮件模板

- 使用纯文本文件(UTF-8 编码)编写邮件内容, 并保存为例如 `template.txt`。
- 可以在模板中使用 `$列名` 形式的占位符, 占位符会替换成收件人 CSV 对应列的值。
- 示例模板: [`examples/template.txt`](examples/template.txt)

```text
Hello $name,

感谢报名我们的活动! 这是一个示例模板。
```

## 3. 准备收件人名单

- 创建一个 CSV 文件(建议使用 Excel 或 WPS 另存为 CSV UTF-8 格式)。
- 第一行需要是列名, 至少包含 `email` 列, 其余列可以用作模板占位符。
- 示例名单: [`examples/recipients.csv`](examples/recipients.csv)

```csv
email,name
alice@example.com,小艾
bob@example.com,小波
```

## 4. 运行脚本

在命令行中进入本仓库目录, 执行:

```bash
python send_emails.py \
    --smtp-server smtp.example.com \
    --port 465 \
    --sender your_account@example.com \
    --subject "Hello $name" \
    --template path/to/template.txt \
    --recipients path/to/recipients.csv
```

脚本会提示输入邮箱密码/授权码(输入时不会显示, 直接敲回车即可)。

> 如果使用 587 端口或服务商要求 STARTTLS, 请额外添加 `--use-starttls`。

## 5. 参数说明

| 参数              | 说明                                                                 |
| ----------------- | -------------------------------------------------------------------- |
| `--smtp-server`   | SMTP 服务器地址, 如 `smtp.qq.com`、`smtp.gmail.com`。                |
| `--port`          | SMTP 端口, 默认 465 (SSL)。若使用 587 需要与 `--use-starttls` 搭配。  |
| `--use-starttls`  | 使用 STARTTLS 加密方式, 常用于 587 端口。                            |
| `--sender`        | 发件邮箱地址, 也是登录用户名。                                       |
| `--reply-to`      | (可选) 回复地址, 如果希望对方回复到其它邮箱。                        |
| `--subject`       | 邮件主题, 支持 `$列名` 占位符。                                      |
| `--template`      | 邮件正文模板路径。                                                   |
| `--recipients`    | 收件人 CSV 路径。                                                     |
| `--dry-run`       | 仅打印生成的邮件, 不真正发送, 用于检查效果。                         |

## 6. 先进行演练 (强烈推荐)

在真正发送之前, 使用 `--dry-run` 参数查看最终邮件的样子:

```bash
python send_emails.py ... --dry-run
```

如果输出中所有信息都正确, 再移除 `--dry-run` 进行正式发送。

## 7. 常见问题

- **SMTP 登录失败**: 请确认已在邮箱后台开启 SMTP 功能, 并使用授权码(不是邮箱登录密码)。
- **模板提示缺少字段**: 根据报错信息检查 CSV 是否包含所需列名, 或者模板中是否拼写错误。
- **中文乱码**: 保存模板和 CSV 时使用 UTF-8 编码即可。

## 8. 进一步定制

脚本基于标准库, 可以根据需要自行扩展, 例如添加附件、嵌入 HTML 邮件等。对于完全零基础用户,
建议先按照上述步骤熟悉基本流程, 再逐步尝试新的功能。

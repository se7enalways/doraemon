#!/usr/bin/env python3
"""Simple bulk email sender based on a text template and CSV recipient list.

This script is designed for non-programmers.  Provide an email template text
file and a CSV file containing your recipients and the script will send an
individual email to each person.

Example template file (template.txt)::

    Subject: 您好 {name}

    这是一封测试邮件, 内容可以写在这里。

Example recipients file (recipients.csv)::

    email,name
    alice@example.com,小红
    bob@example.com,小明

Any column in the CSV file can be referenced from the template using
``{column_name}`` placeholders.  The only required column is ``email``.

To see how the message will look without actually sending anything, run the
script with ``--dry-run``.
"""

from __future__ import annotations

import argparse
import csv
import getpass
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


@dataclass
class Template:
    """Represents the loaded email template."""

    subject: str
    body: str


class TemplateFormatError(ValueError):
    """Raised when the template file is missing the required Subject line."""


def load_template(path: Path) -> Template:
    """Load the subject and body from the template text file."""

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise TemplateFormatError("模板文件是空的, 需要包含Subject行和正文内容。")

    lines = content.splitlines()
    subject_line = lines[0].strip()
    prefix = "subject:"
    if not subject_line.lower().startswith(prefix):
        raise TemplateFormatError(
            "模板文件的第一行必须以 'Subject:' 开头, 例如 'Subject: 您好'"
        )

    subject = subject_line[len(prefix) :].strip()
    # Preserve blank lines between the subject and the body.
    body_lines = lines[1:]
    body = "\n".join(body_lines).lstrip("\n")
    return Template(subject=subject, body=body)


def load_recipients(path: Path) -> List[Dict[str, str]]:
    """Read recipients from a CSV file and ensure the required columns exist."""

    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("收件人清单需要包含表头, 例如: email,name")
        if "email" not in reader.fieldnames:
            raise ValueError("收件人清单必须包含名为 'email' 的列。")

        recipients = []
        for row_number, row in enumerate(reader, start=2):
            email_address = (row.get("email") or "").strip()
            if not email_address:
                raise ValueError(f"第 {row_number} 行缺少 email 地址。")
            recipients.append({key: (value or "").strip() for key, value in row.items()})

    if not recipients:
        raise ValueError("收件人清单为空, 请至少提供一个邮箱地址。")
    return recipients


def render(template: Template, recipient: Dict[str, str]) -> Tuple[str, str]:
    """Fill placeholders in the template using recipient information."""

    try:
        subject = template.subject.format(**recipient)
        body = template.body.format(**recipient)
    except KeyError as exc:  # pragma: no cover - runtime guard
        missing = exc.args[0]
        raise KeyError(
            f"模板中使用了 {{ {missing} }} 占位符, 但在收件人清单中找不到对应的列。"
        ) from exc
    return subject, body


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="根据模板和收件人清单发送批量邮件。",
    )
    parser.add_argument(
        "template",
        type=Path,
        help="包含邮件主题和正文的模板文本文件。",
    )
    parser.add_argument(
        "recipients",
        type=Path,
        help="包含收件人信息的CSV文件, 必须包含 email 列。",
    )
    parser.add_argument(
        "--sender",
        required=True,
        help="发件人邮箱地址 (From)。",
    )
    parser.add_argument(
        "--smtp-host",
        required=True,
        help="SMTP 服务器地址, 例如 smtp.qq.com。",
    )
    parser.add_argument(
        "--smtp-port",
        type=int,
        default=587,
        help="SMTP 服务器端口, 默认 587 (STARTTLS)。",
    )
    parser.add_argument(
        "--smtp-user",
        help="用于登录 SMTP 服务器的用户名, 默认与 --sender 相同。",
    )
    parser.add_argument(
        "--password",
        help="SMTP 登录密码或授权码。未提供时会安全地提示输入。",
    )
    parser.add_argument(
        "--use-ssl",
        action="store_true",
        help="使用 SSL 方式连接 (通常用于端口 465)。",
    )
    parser.add_argument(
        "--no-starttls",
        action="store_true",
        help="禁用 STARTTLS, 仅在服务器明确要求纯文本连接时使用。",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅显示生成的邮件内容, 不真正发送。",
    )
    return parser


def connect_smtp(args: argparse.Namespace) -> smtplib.SMTP:
    """Create the SMTP connection according to the provided arguments."""

    if args.use_ssl:
        server: smtplib.SMTP = smtplib.SMTP_SSL(args.smtp_host, args.smtp_port)
        server.ehlo()
        return server

    server = smtplib.SMTP(args.smtp_host, args.smtp_port)
    server.ehlo()
    if not args.no_starttls:
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
    return server


def send_email(
    server: smtplib.SMTP,
    sender: str,
    recipient: Dict[str, str],
    subject: str,
    body: str,
) -> None:
    """Send a single email message using the provided SMTP server."""

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient["email"]
    message["Subject"] = subject
    message.set_content(body)
    server.send_message(message)


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    template = load_template(args.template)
    recipients = load_recipients(args.recipients)

    password = args.password
    if password is None:
        password = getpass.getpass("请输入 SMTP 登录密码或授权码: ")

    smtp_user = args.smtp_user or args.sender

    if args.dry_run:
        print("[DRY RUN] 以下是将要发送的邮件预览:\n")
        for recipient in recipients:
            subject, body = render(template, recipient)
            print(f"收件人: {recipient['email']}")
            print(f"主题: {subject}")
            print("正文:")
            print(body)
            print("-" * 40)
        return 0

    with connect_smtp(args) as server:
        server.login(smtp_user, password)
        for recipient in recipients:
            subject, body = render(template, recipient)
            send_email(server, args.sender, recipient, subject, body)
            print(f"已发送给 {recipient['email']}")

    print("全部邮件已发送完成。")
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

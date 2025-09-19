"""Utility for sending personalized emails from a template and recipient list.

This script reads an email template and a CSV file containing recipient information
and sends personalized emails to each recipient using SMTP. It relies only on the
Python standard library and is designed to be easy to use for beginners.

Example usage::

    python send_emails.py \
        --smtp-server smtp.example.com \
        --port 465 \
        --sender you@example.com \
        --subject "Hello $name" \
        --template examples/template.txt \
        --recipients examples/recipients.csv

The command will prompt for the email password securely before sending messages.
"""
from __future__ import annotations

import argparse
import csv
import getpass
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from string import Template
from typing import Dict, Iterable, List


class EmailSenderError(Exception):
    """Custom error type for email sender problems."""


def load_template(path: Path) -> Template:
    """Load a text template from *path* and return a :class:`string.Template`.

    Parameters
    ----------
    path:
        Path to a plain text file. The file may contain placeholders such as
        ``$name`` that will be replaced with values from the recipient record.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem errors
        raise EmailSenderError(f"Unable to read template file '{path}': {exc}") from exc
    return Template(content)


def load_recipients(path: Path) -> List[Dict[str, str]]:
    """Load recipient information from a CSV file.

    The CSV file must include a column named ``email``. Additional columns can be
    used as placeholders in the subject and body template.
    """
    try:
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except OSError as exc:  # pragma: no cover - filesystem errors
        raise EmailSenderError(f"Unable to read recipients file '{path}': {exc}") from exc

    if not rows:
        raise EmailSenderError("Recipient list is empty. Add at least one row to the CSV file.")

    missing_email = [idx + 2 for idx, row in enumerate(rows) if not row.get("email")]
    if missing_email:
        raise EmailSenderError(
            "Missing 'email' value in the following CSV rows: "
            + ", ".join(str(number) for number in missing_email)
        )

    return rows


def render_template(template: Template, data: Dict[str, str], *, label: str) -> str:
    """Render *template* using *data* and return the resulting string.

    ``label`` is included in error messages to make troubleshooting easier.
    """
    try:
        return template.substitute(data)
    except KeyError as exc:
        placeholder = exc.args[0]
        raise EmailSenderError(
            f"The template for {label!r} requires the field '${placeholder}',"
            " but it is missing in the recipient data: "
            + ", ".join(sorted(data))
        ) from exc


def create_message(
    *,
    sender: str,
    recipient: Dict[str, str],
    subject_template: Template,
    body_template: Template,
    reply_to: str | None,
) -> EmailMessage:
    """Create and return a fully populated :class:`EmailMessage` instance."""
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient["email"]
    if reply_to:
        message["Reply-To"] = reply_to

    subject = render_template(subject_template, recipient, label="subject")
    body = render_template(body_template, recipient, label="body")

    message["Subject"] = subject
    message.set_content(body)
    return message


def send_messages(
    messages: Iterable[EmailMessage],
    *,
    smtp_server: str,
    port: int,
    username: str,
    password: str,
    use_starttls: bool,
) -> None:
    """Send all *messages* using the provided SMTP server configuration."""
    context = ssl.create_default_context()

    if use_starttls:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls(context=context)
    else:
        server = smtplib.SMTP_SSL(smtp_server, port, context=context)

    with server:
        server.login(username, password)
        for message in messages:
            server.send_message(message)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send personalized emails using a template and a CSV recipient list.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--smtp-server",
        required=True,
        help="Hostname or IP address of the SMTP server (e.g. smtp.gmail.com).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=465,
        help="SMTP server port. Use 465 for SSL or 587 for STARTTLS in most cases.",
    )
    parser.add_argument(
        "--use-starttls",
        action="store_true",
        help="Use STARTTLS instead of an implicit SSL connection.",
    )
    parser.add_argument(
        "--sender",
        required=True,
        help="Email address that appears in the From header.",
    )
    parser.add_argument(
        "--reply-to",
        help="Optional Reply-To address if responses should go to a different inbox.",
    )
    parser.add_argument(
        "--subject",
        required=True,
        help="Email subject. You can reference CSV columns using $placeholders.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        required=True,
        help="Path to the text template file containing the email body.",
    )
    parser.add_argument(
        "--recipients",
        type=Path,
        required=True,
        help="Path to the CSV file containing recipient information.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send emails. Instead, print the generated messages for review.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    body_template = load_template(args.template)
    subject_template = Template(args.subject)
    recipients = load_recipients(args.recipients)

    messages: List[EmailMessage] = []
    for recipient in recipients:
        message = create_message(
            sender=args.sender,
            recipient=recipient,
            subject_template=subject_template,
            body_template=body_template,
            reply_to=args.reply_to,
        )
        messages.append(message)

    if args.dry_run:
        print("Dry run enabled. The following messages would be sent:\n")
        for message in messages:
            print("=" * 72)
            print(message)
        return

    password = getpass.getpass(prompt=f"Password for {args.sender}: ")

    try:
        send_messages(
            messages,
            smtp_server=args.smtp_server,
            port=args.port,
            username=args.sender,
            password=password,
            use_starttls=args.use_starttls,
        )
    except smtplib.SMTPException as exc:  # pragma: no cover - depends on SMTP server
        raise EmailSenderError(f"SMTP error: {exc}") from exc

    print(f"Sent {len(messages)} email(s) successfully.")


if __name__ == "__main__":
    try:
        main()
    except EmailSenderError as error:
        print(f"Error: {error}")
        raise SystemExit(1)

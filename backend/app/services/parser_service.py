import os
import email
from email import policy
from email.parser import BytesParser, Parser
from datetime import datetime, timezone
from typing import Dict, Any, Union


class EmailParserService:
    @staticmethod
    def parse_raw_eml(raw_eml_content: Union[str, bytes]) -> Dict[str, Any]:
        """Parse raw RFC-822 email content or .eml string/bytes into structured data."""
        if isinstance(raw_eml_content, str):
            msg = Parser(policy=policy.default).parsestr(raw_eml_content)
        else:
            msg = BytesParser(policy=policy.default).parsebytes(raw_eml_content)

        subject = msg.get("Subject", "(No Subject)")
        sender = msg.get("From", "unknown@sender.com")
        date_header = msg.get("Date")

        received_at = datetime.now(timezone.utc)
        if date_header:
            try:
                dt = email.utils.parsedate_to_datetime(date_header)
                if dt:
                    received_at = dt
            except Exception:
                pass

        # Extract body
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" not in content_disposition:
                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                            break
                    elif content_type == "text/html" and not body:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(msg.get_content_charset() or "utf-8", errors="replace")
            else:
                body = str(msg.get_payload() or "")

        return {
            "sender": sender.strip(),
            "subject": subject.strip(),
            "body": body.strip(),
            "received_at": received_at,
            "message_id": msg.get("Message-ID", ""),
        }

    @classmethod
    def parse_file(cls, file_path: str) -> Dict[str, Any]:
        """Read and parse an .eml file from disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            content = f.read()

        return cls.parse_raw_eml(content)


parser_service = EmailParserService()

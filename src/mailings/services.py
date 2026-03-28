from __future__ import annotations

from typing import List, Dict, Any, Tuple
from django.db import transaction

from .models import OutgoingEmail
from .utils import validate_row, send_email


class EmailImportService:
    
    @staticmethod
    def process_xlsx_data(data: List[Dict[str, str]]) -> Dict[str, int]:
        stats = {
            "total_rows": len(data),
            "processed_rows": 0,
            "created_records": 0,
            "skipped_records": 0,
            "error_rows": 0,
            "errors": []
        }
        
        for row_num, row in enumerate(data, start=2):
            try:
                if not any(row.values()):
                    stats["skipped_records"] += 1
                    continue
                
                is_valid, error_msg = validate_row(row)
                if not is_valid:
                    stats["error_rows"] += 1
                    stats["errors"].append(f"Строка {row_num}: {error_msg}")
                    continue
                
                if OutgoingEmail.objects.filter(external_id=row["external_id"]).exists():
                    stats["skipped_records"] += 1
                    continue
                
                EmailImportService._create_email_record(row)
                stats["created_records"] += 1
                stats["processed_rows"] += 1
                
            except Exception as e:
                stats["error_rows"] += 1
                error_msg = f"Строка {row_num}: {str(e)}"
                stats["errors"].append(error_msg)
        
        return stats
    
    @staticmethod
    @transaction.atomic
    def _create_email_record(row: Dict[str, str]) -> OutgoingEmail:
        return OutgoingEmail.objects.create(
            external_id=row["external_id"],
            user_id=int(row["user_id"]),
            email=row["email"],
            subject=row["subject"],
            message=row["message"]
        )


class EmailSendingService:
    
    @staticmethod
    def send_pending_emails(limit: int = 100) -> Dict[str, int]:
        stats = {
            "total_processed": 0,
            "sent": 0,
            "errors": 0
        }
        
        pending_emails = OutgoingEmail.objects.filter(
            status=OutgoingEmail.Status.PENDING
        )[:limit]
        
        for email in pending_emails:
            try:
                send_email(email.email, email.subject, email.message)
                email.status = OutgoingEmail.Status.SENT
                email.save()
                stats["sent"] += 1
                
            except Exception as e:
                email.status = OutgoingEmail.Status.ERROR
                email.last_error = str(e)
                email.save()
                stats["errors"] += 1
            
            stats["total_processed"] += 1
        
        return stats

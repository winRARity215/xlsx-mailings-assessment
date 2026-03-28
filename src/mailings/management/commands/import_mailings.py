from __future__ import annotations

import pandas as pd
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError

from mailings.services import EmailImportService


class Command(BaseCommand):

    help = "Импорт рассылок из XLSX и отправка писем (лог + задержка)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("xlsx_path", type=str, help="Путь к XLSX файлу")
        parser.add_argument(
            "--send-emails", 
            action="store_true",
            help="Отправлять письма после импорта"
        )

    def handle(self, *args, **options) -> None:
        xlsx_path = Path(options["xlsx_path"]).expanduser()
        if not xlsx_path.exists():
            raise CommandError(f"Файл не найден: {xlsx_path}")

        try:
            df = pd.read_excel(xlsx_path)
            
            data = df.fillna('').to_dict('records')
            
            stats = EmailImportService.process_xlsx_data(data)
            
            self.stdout.write(self.style.SUCCESS("Результат импорта:"))
            self.stdout.write(f"- обработано строк: {stats['processed_rows']}")
            self.stdout.write(f"- создано записей: {stats['created_records']}")
            self.stdout.write(f"- пропущено записей: {stats['skipped_records']}")
            self.stdout.write(f"- ошибочных строк: {stats['error_rows']}")
            
            if stats['errors']:
                self.stdout.write(self.style.ERROR("Ошибки:"))
                for error in stats['errors'][:10]:
                    self.stdout.write(f"  {error}")
                if len(stats['errors']) > 10:
                    self.stdout.write(f"  ... и еще {len(stats['errors']) - 10} ошибок")
            
            if options['send_emails']:
                from mailings.services import EmailSendingService
                self.stdout.write("\nОтправка писем...")
                send_stats = EmailSendingService.send_pending_emails()
                self.stdout.write(f"- обработано писем: {send_stats['total_processed']}")
                self.stdout.write(f"- отправлено: {send_stats['sent']}")
                self.stdout.write(f"- ошибок: {send_stats['errors']}")
            
        except Exception as e:
            raise CommandError(f"Ошибка при обработке файла: {e}")

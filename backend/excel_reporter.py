import os
from typing import List, Dict, Any
from openpyxl import Workbook
from openpyxl.styles import Font
from .config_manager import ConfigManager
from shared.constants.config_constants import ConfigConstants

class ExcelReporter:
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        paths = config_manager.get_paths_config()
        self.wallets_folder = paths["wallets_folder"]
        
        os.makedirs(self.wallets_folder, exist_ok=True)
    
    def _get_unique_filename(self, token_name: str, t1_str: str, t2_str: str, t3_str: str) -> str:
        
        def format_date_for_filename(date_str):
            try:
                from datetime import datetime
                dt = datetime.strptime(date_str, ConfigConstants.DATE_FORMAT)
                return dt.strftime("%d-%m-%Y")
            except:
                return date_str.replace(" ", "_").replace(":", "").replace("-", "")
        
        t1_formatted = format_date_for_filename(t1_str)
        t2_formatted = format_date_for_filename(t2_str)
        t3_formatted = format_date_for_filename(t3_str)
        
        safe_token_name = token_name.replace("$", "").replace("/", "_").replace("\\", "_").replace(":", "_").replace("*", "_").replace("?", "_").replace("\"", "_").replace("<", "_").replace(">", "_").replace("|", "_")
        
        base_name = os.path.join(self.wallets_folder, f"{safe_token_name}__T1_{t1_formatted}__T2_{t2_formatted}__T3_{t3_formatted}.xlsx")
        
        if not os.path.exists(base_name):
            return base_name
        
        suffix = 1
        while True:
            new_name = os.path.join(self.wallets_folder, f"{safe_token_name}__T1_{t1_formatted}__T2_{t2_formatted}__T3_{t3_formatted}__{suffix}.xlsx")
            if not os.path.exists(new_name):
                return new_name
            suffix += 1
    
    def _create_header_info(self, token_name: str = None) -> List[str]:
        
        config = self.config_manager.config
        
        header_lines = [
            f"TOKEN_CONTRACT_ADDRESS: {config.get('TOKEN_CONTRACT_ADDRESS', 'N/A')}",
            f"T1: {config.get('T1_STR', 'N/A')}",
            f"T2: {config.get('T2_STR', 'N/A')}",
            f"T3: {config.get('T3_STR', 'N/A')}",
            f"NETWORK: {config.get('NETWORK', 'N/A')}"
        ]
        
        if token_name and token_name != "error":
            header_lines.insert(-1, f"TOKEN_NAME: {token_name}")
        
        return header_lines
    
    def _format_cell_value(self, value: Any, column_key: str) -> Any:
        
        if column_key in ["purchased", "final_balance", "native_value", "usd_value"]:
            try:
                return float(value) if value != "error" else value
            except (ValueError, TypeError):
                return value
        
        return value
    
    def _auto_adjust_column_width(self, worksheet) -> None:
        
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                if cell.value:
                    cell_length = len(str(cell.value))
                    max_length = max(max_length, cell_length)
            
            worksheet.column_dimensions[column_letter].width = min(max_length + 2, 50)
    
    def generate_report(self, results: List[Dict[str, Any]], token_name: str, t1_str: str, t2_str: str, t3_str: str) -> str:
        
        filename = self._get_unique_filename(token_name, t1_str, t2_str, t3_str)
        
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "Wallet Analysis"
        
        current_row = 1
        
        config_data = [
            ("", self.config_manager.config.get('TOKEN_CONTRACT_ADDRESS', 'N/A')),
            ("", token_name if token_name != "error" else 'N/A'),
            ("", self.config_manager.config.get('NETWORK', 'N/A')),
            ("", self.config_manager.config.get('T1_STR', 'N/A')),
            ("", self.config_manager.config.get('T2_STR', 'N/A')),
            ("", self.config_manager.config.get('T3_STR', 'N/A'))
        ]
        
        for param, value in config_data:
            worksheet.cell(row=current_row, column=1, value=param)
            worksheet.cell(row=current_row, column=2, value=value)
            current_row += 1
        
        current_row += 2
        
        if results:

            cell = worksheet.cell(row=current_row, column=1, value="NR")
            cell.font = Font(bold=True)
            
            column_headers = list(results[0].keys())
            for col_idx, header in enumerate(column_headers, start=2):
                cell = worksheet.cell(row=current_row, column=col_idx, value=header.upper())
                cell.font = Font(bold=True)
            
            current_row += 1
            
            for row_num, result in enumerate(results, start=1):

                worksheet.cell(row=current_row, column=1, value=row_num)
                
                for col_idx, key in enumerate(column_headers, start=2):
                    value = result.get(key, "")
                    formatted_value = self._format_cell_value(value, key)
                    worksheet.cell(row=current_row, column=col_idx, value=formatted_value)
                
                current_row += 1
        else:

            cell = worksheet.cell(row=current_row, column=1, value="Brak danych")
            cell.font = Font(italic=True, color="FF0000")
        
        worksheet.column_dimensions['A'].width = 5

        worksheet.column_dimensions['B'].width = 60
        
        if results:

            self._auto_adjust_column_width(worksheet)

            worksheet.column_dimensions['A'].width = 5
            worksheet.column_dimensions['B'].width = 60
        
        try:
            workbook.save(filename)
            return filename
        except Exception as e:
            raise Exception(f"Error saving Excel report: {e}")

    def write_excel(self, filename: str, header_lines: List[str], rows: List[Dict[str, Any]]) -> None:
        
        wb = Workbook()
        ws = wb.active
        current_row = 1
        
        for header in header_lines:
            if ":" in header:
                param, value = header.split(":", 1)
                ws.cell(row=current_row, column=1, value=param.strip()).font = Font(bold=True)
                ws.cell(row=current_row, column=2, value=value.strip())
                current_row += 1
        
        current_row += 2
        
        if rows:

            cell = ws.cell(row=current_row, column=1, value="WYNIKI ANALIZY PORTFELI")
            cell.font = Font(bold=True, size=14)
            current_row += 1
            
            current_row += 1
            
            cell = ws.cell(row=current_row, column=1, value="NR")
            cell.font = Font(bold=True)
            
            fieldnames = list(rows[0].keys())
            for col, name in enumerate(fieldnames, start=2):
                cell = ws.cell(row=current_row, column=col, value=name.upper())
                cell.font = Font(bold=True)
            current_row += 1
            
            for row_num, row in enumerate(rows, start=1):

                ws.cell(row=current_row, column=1, value=row_num)
                
                for col, key in enumerate(fieldnames, start=2):
                    value = row.get(key, "")
                    if key in ["purchased", "final_balance", "native_value", "usd_value"]:
                        try:
                            value = float(value)
                        except:
                            pass
                    ws.cell(row=current_row, column=col, value=value)
                current_row += 1
            
            ws.column_dimensions['A'].width = 5

            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter
                if col_letter != 'A':
                    for cell in col:
                        if cell.value:
                            max_length = max(max_length, len(str(cell.value)))
                    ws.column_dimensions[col_letter].width = max_length + 2
            
            if 'B' not in [col[0].column_letter for col in ws.columns if len(col) > 0]:
                ws.column_dimensions['B'].width = 60
        else:
            ws.cell(row=current_row, column=1, value="Brak danych")
            
        ws.column_dimensions['A'].width = 5
        
        wb.save(filename)
    
    def generate_summary_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        
        if not results:
            return {
                "total_wallets": 0,
                "total_purchased": 0,
                "total_final_balance": 0,
                "average_retention": 0,
                "total_usd_value": 0
            }
        
        total_wallets = len(results)
        total_purchased = 0
        total_final_balance = 0
        total_usd_value = 0
        valid_usd_count = 0
        
        for result in results:
            try:
                purchased = float(result.get("purchased", 0))
                final_balance = float(result.get("final_balance", 0))
                total_purchased += purchased
                total_final_balance += final_balance
                
                usd_value = result.get("usd_value", 0)
                if usd_value != "error" and isinstance(usd_value, (int, float)):
                    total_usd_value += float(usd_value)
                    valid_usd_count += 1
                    
            except (ValueError, TypeError):
                continue
        
        average_retention = (
            (total_final_balance / total_purchased * 100) 
            if total_purchased > 0 else 0
        )
        
        return {
            "total_wallets": total_wallets,
            "total_purchased": round(total_purchased, 2),
            "total_final_balance": round(total_final_balance, 2),
            "average_retention": f"{average_retention:.2f}%",
            "total_usd_value": round(total_usd_value, 2),
            "wallets_with_usd_value": valid_usd_count
        }
    
    def print_summary(self, results: List[Dict[str, Any]], execution_time: str = None) -> None:
        
        stats = self.generate_summary_statistics(results)
        
        print("\n" + "="*50)
        print("PODSUMOWANIE ANALIZY")
        print("="*50)
        print(f"Liczba znalezionych portfeli: {stats['total_wallets']}")
        print(f"Łączna ilość zakupionych tokenów: {stats['total_purchased']}")
        print(f"Łączna ilość pozostałych tokenów: {stats['total_final_balance']}")
        print(f"Średni poziom retencji: {stats['average_retention']}")
        
        if stats['wallets_with_usd_value'] > 0:
            print(f"Łączna wartość USD: ${stats['total_usd_value']}")
            print(f"Portfeli z wartością USD: {stats['wallets_with_usd_value']}")
        
        if execution_time:
            print(f"Czas wykonania: {execution_time}")
        
        print("="*50)
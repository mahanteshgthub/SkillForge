import win32com.client as win32
import pythoncom


def convert_excel_to_pdf_silent(xlsx_path, pdf_path):
    """Converts Excel to PDF using COM (must output to disk)."""
    import win32com.client as win32
    import pythoncom

    pythoncom.CoInitialize()
    try:
        excel = win32.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False

        wb = excel.Workbooks.Open(xlsx_path)

        wb.Application.CalculateFull()
        wb.Application.CalculateFullRebuild()

        wb.ExportAsFixedFormat(0, pdf_path)  # ✅ PDF must go to disk

        wb.Close(False)
    finally:
        excel.Quit()
        pythoncom.CoUninitialize()
"""PDF Generator Service - генериране на PDF разписки.

Спринт 3: PDF генериране с поддръжка на кирилица.
"""

from datetime import date, datetime
from io import BytesIO
from typing import Optional

# Използваме reportlab за PDF генериране
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

# Регистрираме кирилични шрифтове
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))


def get_payment_method_label(method: str) -> str:
    """Превежда метода на плащане на български."""
    methods = {
        "cash": "В брой",
        "bank": "Банков превод",
        "card": "Карта",
    }
    return methods.get(method, method)


def format_month(month: str) -> str:
    """Форматира месец от YYYY-MM към българско представяне."""
    months_bg = [
        "Януари", "Февруари", "Март", "Април", "Май", "Юни",
        "Юли", "Август", "Септември", "Октомври", "Ноември", "Декември"
    ]
    try:
        year, month_num = month.split("-")
        month_name = months_bg[int(month_num) - 1]
        return f"{month_name} {year}"
    except (ValueError, IndexError):
        return month


def generate_receipt_pdf(
    receipt_number: str,
    is_copy: bool,
    issued_at: datetime,
    amount: float,
    month: str,
    payment_method: str,
    payment_date: date,
    apartment_number: str,
    owner_name: str,
    issued_by_name: Optional[str] = None,
) -> bytes:
    """Генерира PDF разписка.
    
    Args:
        receipt_number: Номер на разписката
        is_copy: Дали е копие
        issued_at: Дата на издаване
        amount: Сума
        month: Месец за който е плащането
        payment_method: Метод на плащане
        payment_date: Дата на плащане
        apartment_number: Номер на апартамента
        owner_name: Име на собственика
        issued_by_name: Име на издалия
        
    Returns:
        bytes: PDF съдържание
    """
    buffer = BytesIO()
    
    # Размер на разписката (половин A4 или малка)
    width, height = 10 * cm, 14 * cm
    
    c = canvas.Canvas(buffer, pagesize=(width, height))
    
    # Заглавие
    c.setFont("DejaVuSans-Bold", 16)
    title = "Р А З П И С К А"
    c.drawCentredString(width / 2, height - 1.5 * cm, title)
    
    # Номер на разписката
    c.setFont("DejaVuSans-Bold", 12)
    c.drawCentredString(width / 2, height - 2.2 * cm, f"№ {receipt_number}")
    
    # Маркер за копие
    if is_copy:
        c.setFont("DejaVuSans-Bold", 14)
        c.setFillColor(colors.red)
        c.drawCentredString(width / 2, height - 3 * cm, "*** КОПИЕ ***")
        c.setFillColor(colors.black)
        y_start = height - 4 * cm
    else:
        y_start = height - 3.5 * cm
    
    # Данни
    c.setFont("DejaVuSans", 10)
    line_height = 0.6 * cm
    y = y_start
    
    # Дата на издаване
    c.drawString(0.5 * cm, y, f"Дата: {issued_at.strftime('%d.%m.%Y %H:%M')}")
    y -= line_height
    
    c.drawString(0.5 * cm, y, "-" * 45)
    y -= line_height
    
    # Апартамент
    c.drawString(0.5 * cm, y, f"Апартамент: {apartment_number}")
    y -= line_height
    
    # Собственик
    c.drawString(0.5 * cm, y, f"Собственик: {owner_name}")
    y -= line_height
    
    # Месец
    c.drawString(0.5 * cm, y, f"За месец: {format_month(month)}")
    y -= line_height
    
    c.drawString(0.5 * cm, y, "-" * 45)
    y -= line_height
    
    # Сума (по-голям шрифт)
    c.setFont("DejaVuSans-Bold", 14)
    c.drawString(0.5 * cm, y, f"Сума: {amount:.2f} лв.")
    y -= line_height * 1.5
    
    # Метод на плащане
    c.setFont("DejaVuSans", 10)
    c.drawString(0.5 * cm, y, f"Начин: {get_payment_method_label(payment_method)}")
    y -= line_height
    
    # Дата на плащане
    c.drawString(0.5 * cm, y, f"Платено на: {payment_date.strftime('%d.%m.%Y')}")
    y -= line_height
    
    c.drawString(0.5 * cm, y, "-" * 45)
    y -= line_height
    
    # Издал
    if issued_by_name:
        c.drawString(0.5 * cm, y, f"Издал: {issued_by_name}")
    
    # Рамка
    c.setStrokeColor(colors.black)
    c.rect(0.3 * cm, 0.3 * cm, width - 0.6 * cm, height - 0.6 * cm)
    
    c.save()
    
    return buffer.getvalue()

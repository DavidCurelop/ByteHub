from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .base import IInvoiceProvider


class PDFInvoiceProvider(IInvoiceProvider):
    """Generate a PDF invoice for an order using reportlab."""

    def generate(self, order) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph(f'Invoice - Order #{order.pk}', styles['Title']))
        story.append(Spacer(1, 0.4 * cm))

        story.append(Paragraph(
            f"<b>Date:</b> {order.created_at.strftime('%Y-%m-%d %H:%M')}",
            styles['Normal'],
        ))
        story.append(Paragraph(
            f'<b>Status:</b> {order.get_status_display()}',
            styles['Normal'],
        ))
        story.append(Spacer(1, 0.3 * cm))

        customer_name = (
            order.user.get_full_name() or order.user.get_username()
        )
        story.append(Paragraph('<b>Customer</b>', styles['Heading3']))
        story.append(Paragraph(customer_name, styles['Normal']))
        story.append(Paragraph(order.user.email, styles['Normal']))
        if order.shipping_address:
            story.append(Paragraph(
                f'<b>Shipping address:</b> {order.shipping_address}',
                styles['Normal'],
            ))
        story.append(Spacer(1, 0.5 * cm))

        data = [['Product', 'Unit price', 'Quantity', 'Subtotal']]
        for item in order.items.all():
            data.append([
                item.product.name,
                f'${item.unit_price}',
                str(item.quantity),
                f'${item.get_subtotal()}',
            ])

        table = Table(
            data,
            colWidths=[8 * cm, 3 * cm, 2.5 * cm, 3 * cm],
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A2A43')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cfd8dc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
                colors.white, colors.HexColor('#f5f7f8'),
            ]),
        ]))
        story.append(table)
        story.append(Spacer(1, 0.6 * cm))

        totals = [
            ['Subtotal', f'${order.subtotal}'],
            ['Shipping cost', f'${order.shipping_cost}'],
            ['Total', f'${order.total_amount}'],
        ]
        totals_table = Table(totals, colWidths=[4 * cm, 3 * cm], hAlign='RIGHT')
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 0.6, colors.HexColor('#0A2A43')),
        ]))
        story.append(totals_table)

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

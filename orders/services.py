"""
Invoice service layer.

Defines the IInvoiceProvider interface and its PDFInvoiceProvider
implementation using ReportLab.
"""
import abc
import io
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class IInvoiceProvider(abc.ABC):
    """Interface for invoice generation providers."""

    @abc.abstractmethod
    def generate(self, order) -> bytes:
        """Generate an invoice for *order* and return it as raw bytes."""


class PDFInvoiceProvider(IInvoiceProvider):
    """
    Generates a PDF invoice for an Order using ReportLab.

    Usage::

        provider = PDFInvoiceProvider()
        pdf_bytes = provider.generate(order)
    """

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def generate(self, order) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        story = []
        styles = getSampleStyleSheet()

        story += self._build_header(order, styles)
        story.append(Spacer(1, 0.3 * inch))
        story += self._build_customer_info(order, styles)
        story.append(Spacer(1, 0.3 * inch))
        story += self._build_items_table(order, styles)
        story.append(Spacer(1, 0.2 * inch))
        story += self._build_totals(order, styles)

        doc.build(story)
        return buffer.getvalue()

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_header(order, styles):
        elements = []
        title = Paragraph(
            f'<b>ByteHub – Invoice #{order.pk}</b>',
            styles['Title'],
        )
        elements.append(title)
        date_str = (
            order.created_at.strftime('%Y-%m-%d')
            if order.created_at
            else ''
        )
        elements.append(
            Paragraph(f'Date: {date_str}', styles['Normal'])
        )
        return elements

    @staticmethod
    def _build_customer_info(order, styles):
        user = order.user
        full_name = user.get_full_name() or user.email
        lines = [
            '<b>Customer Information</b>',
            f'Name: {full_name}',
            f'Email: {user.email}',
        ]
        if user.phone:
            lines.append(f'Phone: {user.phone}')
        if order.shipping_address:
            addr = order.shipping_address
            lines.append(
                f'Shipping Address: {addr.street}, {addr.city},'
                f' {addr.state} {addr.zip_code}, {addr.country}'
            )
        return [Paragraph(line, styles['Normal']) for line in lines]

    @staticmethod
    def _build_items_table(order, styles):
        header_row = ['Product', 'Qty', 'Unit Price', 'Subtotal']
        rows = [header_row]

        for item in order.items.all():
            rows.append([
                item.product.name,
                str(item.quantity),
                f'${item.unit_price:.2f}',
                f'${item.get_subtotal():.2f}',
            ])

        col_widths = [3 * inch, 0.75 * inch, 1.25 * inch, 1.25 * inch]
        table = Table(rows, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0A2A43')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.white, colors.HexColor('#E2E8E9')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        return [
            Paragraph('<b>Order Items</b>', styles['Heading2']),
            Spacer(1, 0.1 * inch),
            table,
        ]

    @staticmethod
    def _build_totals(order, styles):
        rows = [
            ['Subtotal:', f'${order.subtotal:.2f}'],
            ['Shipping:', f'${order.shipping_cost:.2f}'],
            ['Total:', f'${order.total_amount:.2f}'],
        ]
        totals_table = Table(
            rows,
            colWidths=[5.5 * inch, 0.75 * inch],
        )
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (-1, 2), 12),
            ('LINEABOVE', (0, 2), (-1, 2), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        return [totals_table]

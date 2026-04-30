import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


class PrescriptionPDFService:
    BRAND_COLOR = HexColor('#4F46E5')
    LIGHT_GRAY = HexColor('#F1F5F9')
    DARK_TEXT = HexColor('#1E293B')

    @staticmethod
    def generate_pdf(prescription):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=1.5 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        elements = []

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=20,
            textColor=PrescriptionPDFService.BRAND_COLOR,
            spaceAfter=2 * mm,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#64748B'),
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        )
        heading_style = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontSize=13,
            textColor=PrescriptionPDFService.BRAND_COLOR,
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
        )
        body_style = ParagraphStyle(
            'BodyText',
            parent=styles['Normal'],
            fontSize=10,
            textColor=PrescriptionPDFService.DARK_TEXT,
            leading=14,
        )
        small_style = ParagraphStyle(
            'SmallText',
            parent=styles['Normal'],
            fontSize=8,
            textColor=HexColor('#94A3B8'),
            alignment=TA_CENTER,
        )

        appointment = prescription.appointment
        doctor = appointment.doctor
        patient = appointment.patient

        # Try to get doctor profile
        try:
            doctor_profile = doctor.doctor_profile
        except Exception:
            doctor_profile = None

        # ── Header ──
        elements.append(Paragraph("HealthMeter", title_style))
        elements.append(Paragraph("Healthcare! Everywhere!", subtitle_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=PrescriptionPDFService.BRAND_COLOR))
        elements.append(Spacer(1, 4 * mm))

        # ── Patient / Doctor Info Table ──
        info_data = [
            [
                Paragraph(f"<b>Patient:</b> {patient.get_full_name()}", body_style),
                Paragraph(f"<b>Doctor:</b> Dr. {doctor.get_full_name()}", body_style),
            ],
            [
                Paragraph(f"<b>Date:</b> {appointment.appointment_date.strftime('%d %B %Y')}", body_style),
                Paragraph(f"<b>Specialty:</b> {doctor_profile.specialty if doctor_profile and doctor_profile.specialty else 'General'}", body_style),
            ],
        ]

        info_table = Table(info_data, colWidths=[doc.width / 2] * 2)
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), PrescriptionPDFService.LIGHT_GRAY),
            ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#E2E8F0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 6 * mm))

        # ── Diagnosis ──
        elements.append(Paragraph("Diagnosis", heading_style))
        elements.append(Paragraph(prescription.diagnosis, body_style))

        # ── Rx – Medications ──
        elements.append(Paragraph("Rx — Medications", heading_style))

        items = prescription.items.all()
        if items.exists():
            med_header = ['#', 'Medication', 'Dosage', 'Frequency', 'Duration', 'Notes']
            med_data = [med_header]
            for idx, item in enumerate(items, 1):
                med_data.append([
                    str(idx),
                    Paragraph(item.medication_name, body_style),
                    item.dosage,
                    item.frequency,
                    item.duration,
                    Paragraph(item.notes or '—', body_style),
                ])

            col_widths = [0.06 * doc.width, 0.22 * doc.width, 0.14 * doc.width,
                          0.16 * doc.width, 0.14 * doc.width, 0.28 * doc.width]

            med_table = Table(med_data, colWidths=col_widths, repeatRows=1)
            med_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), PrescriptionPDFService.BRAND_COLOR),
                ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#FFFFFF')),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BACKGROUND', (0, 1), (-1, -1), HexColor('#FFFFFF')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), PrescriptionPDFService.LIGHT_GRAY]),
                ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#CBD5E1')),
                ('INNERGRID', (0, 0), (-1, -1), 0.25, HexColor('#E2E8F0')),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(med_table)
        else:
            elements.append(Paragraph("No medications prescribed.", body_style))

        # ── Instructions ──
        if prescription.instructions:
            elements.append(Paragraph("Instructions", heading_style))
            elements.append(Paragraph(prescription.instructions, body_style))

        # ── Signature ──
        elements.append(Spacer(1, 15 * mm))
        elements.append(HRFlowable(width="40%", thickness=0.5, color=HexColor('#CBD5E1'), hAlign='RIGHT'))

        sig_style = ParagraphStyle('Sig', parent=body_style, alignment=TA_RIGHT)
        sig_text = prescription.doctor_signature_text or f"Dr. {doctor.get_full_name()}"
        elements.append(Paragraph(f"<b>{sig_text}</b>", sig_style))
        if doctor_profile and doctor_profile.license_number:
            elements.append(Paragraph(f"License: {doctor_profile.license_number}", ParagraphStyle('SigSmall', parent=sig_style, fontSize=8, textColor=HexColor('#94A3B8'))))

        # ── Footer ──
        elements.append(Spacer(1, 10 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=HexColor('#E2E8F0')))
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(
            f"Generated by HealthMeter on {prescription.created_at.strftime('%d %B %Y at %I:%M %p')}",
            small_style,
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

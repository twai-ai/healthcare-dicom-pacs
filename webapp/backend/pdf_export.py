"""
PDF Export - Generate comprehensive medical reports from database
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image as RLImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from datetime import datetime
from io import BytesIO
import base64
from pathlib import Path

from database import SessionLocal
import models

class PDFReportGenerator:
    """Generate comprehensive PDF reports from database"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._add_custom_styles()
    
    def _add_custom_styles(self):
        """Add custom styles for medical reports"""
        self.styles.add(ParagraphStyle(
            name='MedicalTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e293b'),
            spaceAfter=12,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2563eb'),
            spaceBefore=12,
            spaceAfter=6,
            leftIndent=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='MedicalBody',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            leftIndent=10
        ))
    
    def generate_patient_report(self, patient_id: str) -> BytesIO:
        """Generate comprehensive PDF report for a patient"""
        
        db = SessionLocal()
        buffer = BytesIO()
        
        try:
            # Get patient data
            patient = db.query(models.Patient).filter(
                models.Patient.patient_id == patient_id
            ).first()
            
            if not patient:
                raise ValueError(f"Patient {patient_id} not found")
            
            # Get related data
            studies = db.query(models.Study).filter(models.Study.patient_id == patient_id).all()
            ai_analyses = db.query(models.AIAnalysis).filter(models.AIAnalysis.patient_id == patient_id).all()
            diagnostic = db.query(models.DiagnosticAnalysis).filter(models.DiagnosticAnalysis.patient_id == patient_id).first()
            
            # Create PDF
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Title
            elements.append(Paragraph("DICOM-AI PLATFORM", self.styles['MedicalTitle']))
            elements.append(Paragraph("Comprehensive Medical Imaging Analysis Report", self.styles['Heading2']))
            elements.append(Spacer(1, 0.3*inch))
            
            # Patient Information
            elements.append(Paragraph("PATIENT INFORMATION", self.styles['SectionHeader']))
            patient_data = [
                ['Patient ID:', patient.patient_id],
                ['Name:', patient.patient_name or 'N/A'],
                ['Age:', f"{patient.patient_age}Y" if patient.patient_age else 'N/A'],
                ['Sex:', patient.patient_sex or 'N/A'],
                ['Report Date:', datetime.now().strftime('%Y-%m-%d %H:%M')]
            ]
            patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
            patient_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('PADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
            ]))
            elements.append(patient_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Diagnostic Assessment
            if diagnostic:
                elements.append(Paragraph("DIAGNOSTIC ASSESSMENT", self.styles['SectionHeader']))
                elements.append(Paragraph(f"<b>COVID-19 Probability Score:</b> {diagnostic.covid_score}/5", self.styles['MedicalBody']))
                elements.append(Paragraph(f"<b>Classification:</b> {diagnostic.covid_probability}", self.styles['MedicalBody']))
                elements.append(Paragraph(f"<b>Severity:</b> {diagnostic.severity}", self.styles['MedicalBody']))
                elements.append(Paragraph(f"<b>Confidence:</b> {diagnostic.confidence}", self.styles['MedicalBody']))
                elements.append(Spacer(1, 0.2*inch))
                
                if diagnostic.clinical_reasoning:
                    elements.append(Paragraph(f"<b>Clinical Reasoning:</b>", self.styles['MedicalBody']))
                    elements.append(Paragraph(diagnostic.clinical_reasoning, self.styles['MedicalBody']))
                    elements.append(Spacer(1, 0.2*inch))
                
                if diagnostic.recommendations:
                    elements.append(Paragraph(f"<b>Recommendations:</b>", self.styles['MedicalBody']))
                    elements.append(Paragraph(diagnostic.recommendations.replace('\n', '<br/>'), self.styles['MedicalBody']))
                
                elements.append(Spacer(1, 0.3*inch))
            
            # AI Analyses
            if ai_analyses:
                elements.append(Paragraph("AI ANALYSIS RESULTS", self.styles['SectionHeader']))
                
                for ai in ai_analyses:
                    elements.append(Paragraph(f"<b>{ai.model_name}</b>", self.styles['Heading3']))
                    
                    # Clean and format findings
                    findings = (ai.findings or '').replace('**', '').replace('*', '')[:2000]
                    elements.append(Paragraph(findings.replace('\n', '<br/>'), self.styles['MedicalBody']))
                    elements.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(elements)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            raise Exception(f"PDF generation failed: {str(e)}")
        finally:
            db.close()


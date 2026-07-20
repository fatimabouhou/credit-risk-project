import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

# -----------------------------
# CONFIGURATION
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGO_DIR = os.path.join(BASE_DIR, "logos")

os.makedirs(DATA_DIR, exist_ok=True)

# Couleurs formelles (Banque Centrale)
BAM_GREEN = colors.HexColor("#006233")
DARK_GREY = colors.HexColor("#333333")
LIGHT_GREY = colors.HexColor("#F0F0F0")

styles = getSampleStyleSheet()

style_header = ParagraphStyle(
    'BAMHeader',
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=BAM_GREEN,
    alignment=1,
    spaceAfter=5
)

style_sub_header = ParagraphStyle(
    'BAMSub',
    fontName='Helvetica-Bold',
    fontSize=12,
    textColor=DARK_GREY,
    alignment=1,
    spaceAfter=20
)

style_section = ParagraphStyle(
    'SectionTitle',
    fontName='Helvetica-Bold',
    fontSize=11,
    textColor=colors.white,
    backColor=BAM_GREEN,
    alignment=0,
    spaceBefore=15,
    spaceAfter=10,
    leftIndent=5,
    borderPadding=4
)

style_info = ParagraphStyle(
    'InfoBox',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.black,
    leading=14,
    spaceAfter=15
)

style_legal = ParagraphStyle(
    'LegalText',
    fontName='Helvetica-Oblique',
    fontSize=8,
    textColor=colors.gray,
    alignment=1,
    spaceBefore=30
)

# -----------------------------
# DONNÉES SYNCHRONISÉES (FIN 2023)
# -----------------------------
def get_engagements_data():
    return [
        ["ÉTABLISSEMENT DÉCLARANT", "NATURE DU CRÉDIT", "AUTORISATION (DH)", "ENCOURS UTILISÉ (DH)"],
        ["ATTIJARIWAFA BANK", "Crédit d'Équipement (Barrage)", "120,000,000", "101,381,696"],
        ["ATTIJARIWAFA BANK", "Crédit Immobilier", "45,000,000", "33,477,432"],
        ["CIH BANK", "Facilité de Caisse / Découvert", "5,000,000", "0"],
        ["TOTAL DES ENGAGEMENTS", "", "170,000,000", "134,859,128"]
    ]

def get_incidents_data():
    return [
        ["DATE INCIDENT", "ÉTABLISSEMENT", "TYPE D'INCIDENT", "MONTANT (DH)", "STATUT"],
        ["-", "-", "NÉANT (Aucun incident déclaré)", "-", "-"]
    ]

def create_table(data, is_total_row=False):
    t = Table(data, colWidths=[45*mm, 55*mm, 35*mm, 35*mm])

    style = [
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_GREY),
        ('TEXTCOLOR', (0, 0), (-1, 0), DARK_GREY),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),

        ('ALIGN', (0, 1), (1, -1), 'LEFT'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]

    # Mise en évidence de la ligne des totaux si applicable
    if is_total_row:
        style.extend([
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), LIGHT_GREY),
        ])

    t.setStyle(TableStyle(style))
    return t

# -----------------------------
# GÉNÉRATION DU PDF
# -----------------------------
def generate_bam_report(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    story = []

    # 1. En-tête Bank Al-Maghrib (Utilisation de logo_BAM.jpg)
    logo_path = os.path.join(LOGO_DIR, "logo_BAM.jpg")
    if os.path.exists(logo_path):
        img = Image(logo_path, width=40*mm, height=40*mm)
        img.hAlign = 'CENTER'
        story.append(img)
    else:
        story.append(Paragraph("BANK AL-MAGHRIB", style_header))
        story.append(Paragraph("بنك المغرب", ParagraphStyle('BAM_AR', fontName='Helvetica-Bold', fontSize=14, textColor=BAM_GREEN, alignment=1)))

    story.append(Spacer(1, 10))
    story.append(Paragraph("CENTRALE DES RISQUES", style_sub_header))
    story.append(Paragraph("RELEVÉ D'INFORMATION CONSOLIDÉ", ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=12, alignment=1)))
    story.append(Spacer(1, 15))

    # 2. Informations du Client (Concordance avec la liasse fiscale)
    story.append(Paragraph("I. IDENTIFICATION DU CLIENT", style_section))

    client_info = """
    <b>Raison Sociale :</b> AGENCE DU BASSIN HYDRAULIQUE DU SEBOU (ABHS)<br/>
    <b>Identifiant Commun de l'Entreprise (ICE) :</b> 001717835000072<br/>
    <b>Identifiant Fiscal :</b> 4510887<br/>
    <b>Registre de Commerce :</b> Non Applicable (Établissement Public)<br/>
    <b>Date d'extraction de la situation :</b> 31/12/2023
    """
    story.append(Paragraph(client_info, style_info))

    # 3. Tableau des Engagements (Dettes)
    story.append(Paragraph("II. SITUATION DES ENGAGEMENTS DÉCLARÉS", style_section))
    story.append(create_table(get_engagements_data(), is_total_row=True))
    story.append(Spacer(1, 20))

    # 4. Tableau des Incidents de Paiement
    story.append(Paragraph("III. CENTRALE DES INCIDENTS DE PAIEMENT (CIP)", style_section))
    story.append(create_table(get_incidents_data(), is_total_row=False))

    # 5. Footer légal de la Banque Centrale
    legal_text = """
    Document délivré à titre strictement confidentiel conformément à la loi bancaire en vigueur.<br/>
    Bank Al-Maghrib décline toute responsabilité quant à l'exactitude des informations déclarées par les établissements de crédit.<br/>
    *** FIN DU RELEVÉ ***
    """
    story.append(Paragraph(legal_text, style_legal))

    doc.build(story)
    print(f"✅ Relevé de la Centrale des Risques (BAM) généré avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "releve_central_risques.pdf")
    generate_bam_report(output_path)
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode import qr

# -----------------------------
# CONFIGURATION ET STYLES
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGO_DIR = os.path.join(BASE_DIR, "logos")

os.makedirs(DATA_DIR, exist_ok=True)

# Couleurs officielles (Bleu CNSS)
BLUE_CNSS = colors.HexColor("#00519E")
GREY_TEXT = colors.HexColor("#4A4A4A")
LIGHT_GREY = colors.HexColor("#F5F5F5")

styles = getSampleStyleSheet()

style_header_left = ParagraphStyle(
    'HeaderLeft',
    fontName='Helvetica-Bold',
    fontSize=9,
    textColor=BLUE_CNSS,
    alignment=0,
    leading=12
)

style_header_right = ParagraphStyle(
    'HeaderRight',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.black,
    alignment=2,
    spaceAfter=20
)

style_title = ParagraphStyle(
    'DocTitle',
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=BLUE_CNSS,
    alignment=1,
    spaceBefore=30,
    spaceAfter=10
)

style_subtitle = ParagraphStyle(
    'DocSubTitle',
    fontName='Helvetica-Bold',
    fontSize=12,
    textColor=colors.black,
    alignment=1,
    spaceAfter=30
)

style_body = ParagraphStyle(
    'BodyText',
    fontName='Helvetica',
    fontSize=11,
    textColor=colors.black,
    leading=16,
    alignment=4,
    spaceAfter=15
)

style_bold_center = ParagraphStyle(
    'BoldCenter',
    fontName='Helvetica-Bold',
    fontSize=12,
    textColor=colors.black,
    alignment=1,
    spaceBefore=10,
    spaceAfter=20
)

style_footer = ParagraphStyle(
    'FooterText',
    fontName='Helvetica',
    fontSize=8,
    textColor=GREY_TEXT,
    alignment=1,
    leading=10
)

style_table_cell = ParagraphStyle(
    'TableCell',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.black,
    leading=12
)

# -----------------------------
# GÉNÉRATION DU PDF
# -----------------------------
def generate_cnss_certificate(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    story = []

    # 1. En-tête (Logo CNSS + Date)
    logo_cnss_path = os.path.join(LOGO_DIR, "logo_cnss.png")

    # Logo CNSS (Gauche)
    if os.path.exists(logo_cnss_path):
        img_cnss = Image(logo_cnss_path, width=40*mm, height=25*mm, kind='proportional')
        img_cnss.hAlign = 'LEFT'
    else:
        img_cnss = Paragraph("<b>Caisse Nationale de<br/>Sécurité Sociale</b>", style_header_left)

    header_data = [
        [
            img_cnss,
            Paragraph("Casablanca, le 29/12/2023<br/><b>Réf Damancom :<br/>AT-2023-8849201</b>", style_header_right)
        ]
    ]

    t_header = Table(header_data, colWidths=[80*mm, 80*mm])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    story.append(t_header)

    # Ligne de séparation
    story.append(Spacer(1, 15))
    t_line = Table([['']], colWidths=[160*mm], rowHeights=[1])
    t_line.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,-1), 1, BLUE_CNSS)]))
    story.append(t_line)

    # 2. Titre du document
    story.append(Paragraph("ATTESTATION DE MISE À JOUR", style_title))
    story.append(Paragraph("(Délivrée pour servir aux soumissions, marchés et banques)", style_subtitle))

    # 3. Corps du texte
    story.append(Paragraph("Le Directeur Général de la Caisse Nationale de Sécurité Sociale atteste que l'employeur désigné ci-après :", style_body))

    # 4. Informations de l'entreprise (Identifiants officiels CNSS)
    client_data = [
        ["Raison sociale :", Paragraph("AGENCE DU BASSIN HYDRAULIQUE DU SEBOU", style_table_cell)],
        ["N° d'Affiliation CNSS :", Paragraph("<b>8765432</b>", style_table_cell)], # Le matricule CNSS a 7 chiffres
        ["Identifiant Commun de l'Entreprise (ICE) :", Paragraph("001717835000072", style_table_cell)],
        ["Siège social :", Paragraph("ANGLE ABOU EL ALAE EL MAARI ET AHMED CHAOUKI BP 2101 FES", style_table_cell)]
    ]

    t_client = Table(client_data, colWidths=[70*mm, 90*mm])
    t_client.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('BACKGROUND', (0, 0), (0, -1), LIGHT_GREY)
    ]))
    story.append(t_client)
    story.append(Spacer(1, 20))

    # 5. Mention de régularité CNSS
    attestation_text = """
    <b>Est en règle</b> vis-à-vis de la Caisse Nationale de Sécurité Sociale en matière de 
    déclarations de salaires et de paiement des cotisations, majorations et pénalités de retard y afférentes 
    arrêtées à la date du <b>30/11/2023</b>.
    """
    story.append(Paragraph(attestation_text, style_body))
    story.append(Paragraph("La présente attestation est délivrée à l'intéressé(e) pour servir et valoir ce que de droit.", style_body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Attestation générée électroniquement via le portail DAMANCOM", style_bold_center))

    # 6. QR Code simulé pour vérification DAMANCOM
    qr_code = qr.QrCodeWidget('https://www.damancom.ma/verif/AT-2023-8849201')
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(45, 45, transform=[45/width,0,0,45/height,0,0])
    d.add(qr_code)

    # Layout pour signature et QR Code
    signature_data = [
        [d, Paragraph("<b>Pôle Entreprises - Direction des Affiliés</b><br/>Code d'authenticité : DAM-8849201-XYZ", style_header_left)]
    ]
    t_sig = Table(signature_data, colWidths=[50*mm, 110*mm])
    t_sig.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT')
    ]))
    story.append(Spacer(1, 20))
    story.append(t_sig)

    # 7. Footer de sécurité
    story.append(Spacer(1, 40))
    footer_text = """
    L'authenticité de cette attestation peut être vérifiée sur le portail www.damancom.ma, rubrique "Vérification des attestations".<br/>
    Conformément aux dispositions de la loi 09-08, les traitements des données à caractère personnel sont protégés.
    """
    story.append(Paragraph(footer_text, style_footer))

    doc.build(story)
    print(f"✅ Attestation CNSS Damancom générée avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "attestation_cnss_2023.pdf")
    generate_cnss_certificate(output_path)
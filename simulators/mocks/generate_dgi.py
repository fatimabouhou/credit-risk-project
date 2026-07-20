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

BLUE_DGI = colors.HexColor("#004B87")
GREY_TEXT = colors.HexColor("#4A4A4A")
LIGHT_GREY = colors.HexColor("#F5F5F5")

styles = getSampleStyleSheet()

style_header_left = ParagraphStyle(
    'HeaderLeft',
    fontName='Helvetica-Bold',
    fontSize=9,
    textColor=BLUE_DGI,
    alignment=0, # Left
    leading=12
)

style_header_right = ParagraphStyle(
    'HeaderRight',
    fontName='Helvetica',
    fontSize=10,
    textColor=colors.black,
    alignment=2, # Right
    spaceAfter=20
)

style_title = ParagraphStyle(
    'DocTitle',
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=colors.black,
    alignment=1, # Center
    spaceBefore=30,
    spaceAfter=30
)

style_body = ParagraphStyle(
    'BodyText',
    fontName='Helvetica',
    fontSize=11,
    textColor=colors.black,
    leading=16,
    alignment=4, # Justified
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

# Nouveau style pour le texte à l'intérieur du tableau pour forcer le retour à la ligne
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
def generate_dgi_certificate(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=25*mm,
        leftMargin=25*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    story = []

    # 1. En-tête (Logos + Date)
    logo_dgi_path = os.path.join(LOGO_DIR, "dgi.png")
    armoiries_path = os.path.join(LOGO_DIR, "maroc.png")

    # Logo DGI (Gauche)
    if os.path.exists(logo_dgi_path):
        img_dgi = Image(logo_dgi_path, width=40*mm, height=20*mm, kind='proportional')
        img_dgi.hAlign = 'LEFT'
    else:
        img_dgi = Paragraph("ROYAUME DU MAROC<br/><b>DGI</b>", style_header_left)

    # Armoiries (Centre)
    if os.path.exists(armoiries_path):
        img_arm = Image(armoiries_path, width=25*mm, height=25*mm, kind='proportional')
        img_arm.hAlign = 'CENTER'
    else:
        img_arm = Paragraph("<b>ROYAUME DU MAROC</b>", style_bold_center)

    header_data = [
        [
            img_dgi,
            img_arm,
            Paragraph("Rabat, le 28/12/2023<br/><b>N° de référence :<br/>2023-SIMPL-987654321</b>", style_header_right)
        ]
    ]

    t_header = Table(header_data, colWidths=[55*mm, 50*mm, 55*mm])
    t_header.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
    ]))
    story.append(t_header)

    # Ligne de séparation
    story.append(Spacer(1, 15))
    t_line = Table([['']], colWidths=[160*mm], rowHeights=[1])
    t_line.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,-1), 1, BLUE_DGI)]))
    story.append(t_line)

    # 2. Titre du document
    story.append(Paragraph("ATTESTATION DE RÉGULARITÉ FISCALE", style_title))

    # 3. Corps du texte
    story.append(Paragraph("Le Directeur Général des Impôts atteste que le contribuable désigné ci-après :", style_body))

    # 4. Informations de l'entreprise (Identifiants officiels)
    # L'utilisation de Paragraph() ici force le retour à la ligne automatique
    client_data = [
        ["Raison sociale :", Paragraph("AGENCE DU BASSIN HYDRAULIQUE DU SEBOU", style_table_cell)],
        ["Identifiant Commun de l'Entreprise (ICE) :", Paragraph("001717835000072", style_table_cell)],
        ["Identifiant Fiscal (IF) :", Paragraph("4510887", style_table_cell)],
        ["Taxe Professionnelle :", Paragraph("13606841", style_table_cell)],
        ["Siège social :", Paragraph("ANGLE ABOU EL ALAE EL MAARI ET AHMED CHAOUKI BP 2101 FES", style_table_cell)]
    ]

    t_client = Table(client_data, colWidths=[85*mm, 75*mm])
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

    # 5. Mention de régularité
    attestation_text = """
    <b>Est en règle</b>, à la date de délivrance de la présente attestation, au regard de ses obligations 
    de déclaration et de paiement des impôts, droits et taxes dont elle est redevable vis-à-vis de 
    l'Administration Fiscale.
    """
    story.append(Paragraph(attestation_text, style_body))
    story.append(Paragraph("La présente attestation est délivrée pour servir et valoir ce que de droit.", style_body))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Document généré électroniquement via les téléservices SIMPL", style_bold_center))

    # 6. QR Code simulé pour vérification
    qr_code = qr.QrCodeWidget('https://simpl-recherche.tax.gov.ma/verif/2023-SIMPL-987654321')
    bounds = qr_code.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    d = Drawing(45, 45, transform=[45/width,0,0,45/height,0,0])
    d.add(qr_code)

    # Layout pour signature et QR Code
    signature_data = [
        [d, Paragraph("<b>Signature Numérique</b><br/>Direction Générale des Impôts<br/>Code de vérification : 7A8B9C2D", style_header_left)]
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
    Les informations contenues dans cette attestation peuvent être vérifiées sur le portail de la Direction Générale des Impôts : www.tax.gov.ma<br/>
    Toute falsification ou modification du présent document expose son auteur aux poursuites pénales prévues par la loi.
    """
    story.append(Paragraph(footer_text, style_footer))

    doc.build(story)
    print(f"✅ Attestation DGI SIMPL avec logos générée avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "attestation_dgi_2023.pdf")
    generate_dgi_certificate(output_path)
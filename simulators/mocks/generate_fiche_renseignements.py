import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

# -----------------------------
# CONFIGURATION ET STYLES
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

BLUE_CORP = colors.HexColor("#004B87")
LIGHT_BLUE = colors.HexColor("#EAF1F8")
LIGHT_GREY = colors.HexColor("#F9F9F9")

styles = getSampleStyleSheet()

style_title = ParagraphStyle(
    'DocTitle',
    fontName='Helvetica-Bold',
    fontSize=16,
    textColor=BLUE_CORP,
    alignment=1, # Center
    spaceBefore=20,
    spaceAfter=30
)

style_table_key = ParagraphStyle(
    'TableKey',
    fontName='Helvetica-Bold',
    fontSize=11,
    textColor=colors.black,
    leading=14
)

style_table_value = ParagraphStyle(
    'TableValue',
    fontName='Helvetica',
    fontSize=11,
    textColor=colors.black,
    leading=14
)

# -----------------------------
# GÉNÉRATION DU PDF
# -----------------------------
def generate_fiche_renseignements(filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=20*mm,
        leftMargin=20*mm,
        topMargin=20*mm,
        bottomMargin=20*mm
    )

    story = []

    # Titre du document
    story.append(Paragraph("FICHE DE RENSEIGNEMENTS ENTREPRISE", style_title))

    # Données de la fiche
    data = [
        [Paragraph("Raison sociale :", style_table_key), Paragraph("<b>ABHS SARL</b>", style_table_value)],
        [Paragraph("Forme juridique :", style_table_key), Paragraph("Société à Responsabilité Limitée (SARL)", style_table_value)],
        [Paragraph("Capital social :", style_table_key), Paragraph("1 000 000,00 MAD", style_table_value)],
        [Paragraph("Adresse :", style_table_key), Paragraph("Zone Industrielle Bir Rami, Lot n° 45, Kénitra", style_table_value)],
        [Paragraph("Téléphone :", style_table_key), Paragraph("+212 5 37 32 44 11", style_table_value)],
        [Paragraph("Email :", style_table_key), Paragraph("contact@abhs-sarl.ma", style_table_value)],
        [Paragraph("Nombre d'employés :", style_table_key), Paragraph("18 collaborateurs", style_table_value)],
        [Paragraph("Date de création :", style_table_key), Paragraph("12/04/2018", style_table_value)],
        [Paragraph("Activité :", style_table_key), Paragraph("Commerce de matériaux de construction", style_table_value)],
        [Paragraph("Actionnaires :", style_table_key), Paragraph("&bull; Mohamed El Amrani (Gérant) : 80%<br/>&bull; Youssef El Amrani : 20%", style_table_value)]
    ]

    # Création du tableau
    t_fiche = Table(data, colWidths=[60*mm, 110*mm])

    # Style du tableau (Lignes alternées pour un effet "formulaire" propre)
    table_style = [
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]

    # Alternance de couleurs (Gris très clair / Blanc)
    for i in range(len(data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), LIGHT_GREY))
        else:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.white))

    # Première colonne en bleu très clair pour faire ressortir les clés
    table_style.append(('BACKGROUND', (0, 0), (0, -1), LIGHT_BLUE))

    t_fiche.setStyle(TableStyle(table_style))
    story.append(t_fiche)

    # Date et mention en bas de page
    story.append(Spacer(1, 20*mm))
    style_footer = ParagraphStyle('Footer', fontName='Helvetica-Oblique', fontSize=9, alignment=2, textColor=colors.grey)
    story.append(Paragraph("Fiche éditée et certifiée exacte le 15 Décembre 2023", style_footer))

    doc.build(story)
    print(f"✅ Fiche de renseignements générée avec succès : {filename}")

if __name__ == "__main__":
    output_path = os.path.join(DATA_DIR, "fiche_renseignements.pdf")
    generate_fiche_renseignements(output_path)